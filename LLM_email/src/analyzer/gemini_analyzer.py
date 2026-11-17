import json
from typing import List, Optional
from google import genai
from google.genai import types

from src.models import EmailAnalysis, ProcessedEmail, RawEmail


class GeminiEmailAnalyzer:
    """Google Gemini (AI Studio) API kliens az emailek intelligens kategorizálásához,
    priorizálásához és a strukturált napi összefoglaló (Daily Digest) összeállításához."""

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.session_tokens_used: int = 0
        self.session_requests_used: int = 0

    def test_connection(self) -> bool:
        """Teszteli a Gemini API kapcsolatot egy rövid kéréssel."""
        if not self.client:
            print("[ERROR] Nincs megadva GEMINI_API_KEY.")
            return False

        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents="Ping",
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                ),
            )
            return bool(resp.text)
        except Exception as e:
            print(f"[ERROR] Gemini API kapcsolódási hiba: {e}")
            return False

    def analyze_email(self, raw_email: RawEmail) -> EmailAnalysis:
        """Elemzi az emailt: kategória, sürgősség, kötelező válasz, hírérték, prioritás pontszám és összefoglaló."""
        if not self.client:
            return EmailAnalysis(
                category=raw_email.default_category,
                summary="Nem érhető el a Gemini API az elemzéshez.",
            )

        system_instruction = (
            "Egy intelligens személyes email asszisztens vagy. Feladatod a beérkező levél szigorú elemzése "
            "és strukturált JSON formátumban való visszaadása.\n"
            "Kiemelten fontos feladatok:\n"
            "1. Határozd meg, hogy KÖTELEZŐ-E vagy erősen ajánlott-e válaszolni a levélre ('needs_reply': true/false).\n"
            "   (Pl. közvetlen kérdés, megbízás, kérés, feladat esetén true; hírlevelek, automatikus értesítők esetén false).\n"
            "2. Határozd meg, hogy a levél tartalmaz-e érdekes, releváns hírt, szakmai összefoglalót vagy újdonságot ('is_interesting_news': true/false).\n"
            "3. Adj egy 1-10-es prioritási pontszámot ('priority_score'): 10 ha azonnali/sürgős teendő vagy kötelező válasz, 1 ha érdektelen spam/értesítő.\n"
            "4. Gyűjtsd ki a konkrét teendőket ('action_items') és határidőket ('deadlines').\n"
            "5. Írj 1-2 tömör magyar mondatos összefoglalót ('summary').\n\n"
            "JSON formátum:\n"
            "{\n"
            '  "category": "személyes" | "munka" | "egyetem" | "projekt" | "hírlevél/cikk" | "értesítő" | "egyéb",\n'
            '  "urgency": "kritikus" | "magas" | "közepes" | "alacsony",\n'
            '  "importance": "kiemelt" | "normál" | "alacsony",\n'
            '  "needs_reply": true | false,\n'
            '  "is_interesting_news": true | false,\n'
            '  "priority_score": 1..10,\n'
            '  "summary": "Magyar nyelvű lényeg 1-2 mondatban.",\n'
            '  "action_items": ["teendő 1"],\n'
            '  "deadlines": ["időpont vagy határidő"]\n'
            "}"
        )

        user_content = (
            f"Fiók: {raw_email.account_name}\n"
            f"Feladó: {raw_email.sender}\n"
            f"Címzett: {raw_email.recipient}\n"
            f"Dátum: {raw_email.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Tárgy: {raw_email.subject}\n\n"
            f"Levél szövege:\n{raw_email.body_text[:4000]}"
        )

        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except Exception as primary_err:
            # Ha a választott modell túlterhelt (503/429), próbáljuk meg a tartalék modellel (gemini-2.5-flash vagy gemini-3.8-flash)
            fallback_models = ["gemini-2.5-flash", "gemini-3.8-flash"]
            resp = None
            for fb_model in fallback_models:
                if fb_model == self.model:
                    continue
                try:
                    resp = self.client.models.generate_content(
                        model=fb_model,
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                    break
                except Exception:
                    continue

            if resp is None:
                print(f"[WARN] Hiba a Gemini elemzés során ({raw_email.subject}): {primary_err}")
                return EmailAnalysis(
                    category=raw_email.default_category,
                    urgency="közepes",
                    importance="normál",
                    needs_reply=False,
                    is_interesting_news=False,
                    priority_score=5,
                    summary=f"{raw_email.sender}: {raw_email.subject}",
                    action_items=[],
                    deadlines=[],
                )

            self.session_requests_used += 1
            if resp.usage_metadata and resp.usage_metadata.total_token_count:
                self.session_tokens_used += resp.usage_metadata.total_token_count

            response_text = resp.text or "{}"
            data = json.loads(response_text)

            category = data.get("category", raw_email.default_category)
            valid_cats = ["személyes", "munka", "egyetem", "projekt", "hírlevél/cikk", "értesítő", "egyéb"]
            if category not in valid_cats:
                category = raw_email.default_category

            urgency = data.get("urgency", "közepes")
            if urgency not in ["kritikus", "magas", "közepes", "alacsony"]:
                urgency = "közepes"

            importance = data.get("importance", "normál")
            if importance not in ["kiemelt", "normál", "alacsony"]:
                importance = "normál"

            needs_reply = bool(data.get("needs_reply", False))
            is_interesting_news = bool(data.get("is_interesting_news", False))
            priority_score = int(data.get("priority_score", 5))
            priority_score = max(1, min(10, priority_score))

            summary = data.get("summary") or f"{raw_email.sender}: {raw_email.subject}"
            action_items = data.get("action_items") if isinstance(data.get("action_items"), list) else []
            deadlines = data.get("deadlines") if isinstance(data.get("deadlines"), list) else []

            return EmailAnalysis(
                category=category,
                urgency=urgency,
                importance=importance,
                needs_reply=needs_reply,
                is_interesting_news=is_interesting_news,
                priority_score=priority_score,
                summary=summary,
                action_items=[str(item) for item in action_items if item],
                deadlines=[str(dl) for dl in deadlines if dl],
            )
        except Exception as e:
            print(f"[WARN] Hiba a Gemini elemzés során ({raw_email.subject}): {e}")
            return EmailAnalysis(
                category=raw_email.default_category,
                urgency="közepes",
                importance="normál",
                needs_reply=False,
                is_interesting_news=False,
                priority_score=5,
                summary=f"{raw_email.sender}: {raw_email.subject}",
                action_items=[],
                deadlines=[],
            )

    def generate_daily_digest(self, processed_emails: List[ProcessedEmail]) -> str:
        """Összeállít egy intelligensen priorizált Daily Digest összefoglalót:
        1. Kötelező / Sürgős válaszok elöl
        2. Határidők és egyéb teendők
        3. Legérdekesebb és legrelevánsabb hírek/hírlevelek
        4. Egyéb beérkezett emailek kategóriák szerint."""
        if not processed_emails:
            return "📬 Ma nem érkezett új feldolgozandó email a figyelt fiókokba."

        # Rendezzük a leveleket prioritási pontszám szerint csökkenő sorrendbe
        sorted_emails = sorted(
            processed_emails,
            key=lambda item: (
                1 if item.analysis.needs_reply else 0,
                item.analysis.priority_score,
                1 if item.analysis.urgency in ["kritikus", "magas"] else 0,
            ),
            reverse=True,
        )

        must_reply: List[ProcessedEmail] = [e for e in sorted_emails if e.analysis.needs_reply]
        interesting_news: List[ProcessedEmail] = [
            e for e in sorted_emails if e.analysis.is_interesting_news or e.analysis.category == "hírlevél/cikk"
        ]
        other_urgent: List[ProcessedEmail] = [
            e for e in sorted_emails if e not in must_reply and e.analysis.urgency in ["kritikus", "magas"]
        ]

        all_deadlines: List[str] = []
        all_actions: List[str] = []
        for e in sorted_emails:
            for dl in e.analysis.deadlines:
                all_deadlines.append(f"• {dl} (Levél: {e.raw.subject} - {e.raw.account_name})")
            for act in e.analysis.action_items:
                all_actions.append(f"• {act} (Levél: {e.raw.subject})")

        lines: List[str] = []
        lines.append(f"📬 Napi Email Digest ({len(processed_emails)} új levél)")
        lines.append("=" * 32)

        # 1. KÖTELEZŐ / FONTOS VÁLASZOK (Top prioritás)
        if must_reply:
            lines.append(f"\n💬 VÁLASZT IGÉNYLŐ LEVELEK ({len(must_reply)} db):")
            for mail in must_reply:
                lines.append(f"• [{mail.raw.account_name}] {mail.raw.sender}: {mail.raw.subject}")
                lines.append(f"  👉 Lényeg: {mail.analysis.summary}")

        # 2. SÜRGŐS ÉRTESÍTÉSEK
        if other_urgent:
            lines.append(f"\n🚨 EGYÉB SÜRGŐS ({len(other_urgent)} db):")
            for mail in other_urgent:
                lines.append(f"• [{mail.analysis.urgency.upper()}] {mail.raw.subject} ({mail.raw.account_name})")
                lines.append(f"  👉 {mail.analysis.summary}")

        # 3. HATÁRIDŐK
        if all_deadlines:
            lines.append(f"\n📅 HATÁRIDŐK & DÁTUMOK:")
            lines.extend(all_deadlines[:6])

        # 4. TEENDŐK
        if all_actions:
            lines.append(f"\n✅ TEENDŐK:")
            lines.extend(all_actions[:6])
            if len(all_actions) > 6:
                lines.append(f"  ...és további {len(all_actions) - 6} teendő.")

        # 5. LEGÉRDEKESEBB HÍREK / RELEVÁNS HÍRLEVELEK
        if interesting_news:
            lines.append(f"\n💡 RELEVÁNS HÍREK & CIKKEK:")
            for mail in interesting_news[:4]:
                lines.append(f"• {mail.raw.subject} ({mail.raw.sender})")
                lines.append(f"  📖 {mail.analysis.summary}")

        # 6. ÖSSZESÍTŐ STATISZTIKA
        lines.append(f"\n📊 Röviden:")
        lines.append(f"Összesen {len(processed_emails)} új levél ({len(must_reply)} válaszra vár, {len(all_deadlines)} határidő).")

        return "\n".join(lines)
