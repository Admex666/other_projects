import json
from typing import List, Optional
from groq import Groq

from src.models import EmailAnalysis, ProcessedEmail, RawEmail


class GroqEmailAnalyzer:
    """Groq API kliens az emailek intelligens kategorizálásához és elemzéséhez."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b"):
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key) if api_key else None
        self.last_rate_limits: dict = {}
        self.session_tokens_used: int = 0
        self.session_requests_used: int = 0

    def get_rate_limits(self) -> dict:
        """Lekéri az aktuális Groq API limiteket és a hátralévő keretet."""
        if not self.client:
            return {}

        try:
            raw_resp = self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            headers = raw_resp.headers
            limits = {
                "limit_requests": headers.get("x-ratelimit-limit-requests", "N/A"),
                "remaining_requests": headers.get("x-ratelimit-remaining-requests", "N/A"),
                "reset_requests": headers.get("x-ratelimit-reset-requests", "N/A"),
                "limit_tokens": headers.get("x-ratelimit-limit-tokens", "N/A"),
                "remaining_tokens": headers.get("x-ratelimit-remaining-tokens", "N/A"),
                "reset_tokens": headers.get("x-ratelimit-reset-tokens", "N/A"),
            }
            self.last_rate_limits = limits
            return limits
        except Exception as e:
            print(f"[WARN] Nem sikerült lekérni a rate limiteket: {e}")
            return {}

    def test_connection(self) -> bool:
        """Teszteli a Groq API elérhetőségét egy egyszerű kérdéssel."""
        if not self.client:
            print("[ERROR] Nincs megadva GROQ_API_KEY.")
            return False

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Ping"}],
                max_tokens=5,
            )
            return bool(response.choices and response.choices[0].message.content)
        except Exception as e:
            print(f"[ERROR] Groq API kapcsolódási hiba: {e}")
            return False

    def analyze_email(self, raw_email: RawEmail) -> EmailAnalysis:
        """Elemzi a nyers emailt: kategória, sürgősség, teendők, határidők és összefoglaló."""
        if not self.client:
            return EmailAnalysis(
                category=raw_email.default_category,
                summary="Nem érhető el a Groq API az elemzéshez.",
            )

        system_prompt = (
            "Egy professzionális személyes email asszisztens vagy. Feladatod a beérkező email elemzése és "
            "szigorúan érvényes JSON formátumban való visszaadása.\n"
            "A kimenet sémája:\n"
            "{\n"
            '  "category": "személyes" | "munka" | "egyetem" | "projekt" | "egyéb",\n'
            '  "urgency": "kritikus" | "magas" | "közepes" | "alacsony",\n'
            '  "importance": "kiemelt" | "normál" | "alacsony",\n'
            '  "summary": "Rövid, pontos magyar összefoglaló (max 2 mondat).",\n'
            '  "action_items": ["konkrét teendő 1", "konkrét teendő 2"],\n'
            '  "deadlines": ["2026-09-10 14:00 - jelentkezés", "holnap délután"]\n'
            "}\n"
            "Szabályok:\n"
            "- A válasz nyelve kizárólag magyar legyen.\n"
            "- Ha nincs teendő vagy határidő, üres listát adj vissza.\n"
            "- Az alapértelmezett kategória javaslat a fiók alapján: "
            f"'{raw_email.default_category}', de a tartalom alapján felülbírálhatod.\n"
            "- Csak a tiszta JSON objektumot add vissza!"
        )

        user_content = (
            f"Fiók: {raw_email.account_name}\n"
            f"Feladó: {raw_email.sender}\n"
            f"Címzett: {raw_email.recipient}\n"
            f"Dátum: {raw_email.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Tárgy: {raw_email.subject}\n\n"
            f"Tartalom:\n{raw_email.body_text[:3500]}"
        )

        try:
            raw_resp = self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            # Frissítjük a rate limit adatokat és tokeneket
            headers = raw_resp.headers
            self.last_rate_limits = {
                "limit_requests": headers.get("x-ratelimit-limit-requests", "N/A"),
                "remaining_requests": headers.get("x-ratelimit-remaining-requests", "N/A"),
                "reset_requests": headers.get("x-ratelimit-reset-requests", "N/A"),
                "limit_tokens": headers.get("x-ratelimit-limit-tokens", "N/A"),
                "remaining_tokens": headers.get("x-ratelimit-remaining-tokens", "N/A"),
                "reset_tokens": headers.get("x-ratelimit-reset-tokens", "N/A"),
            }
            self.session_requests_used += 1

            completion = raw_resp.parse()
            if completion.usage:
                self.session_tokens_used += completion.usage.total_tokens

            response_content = completion.choices[0].message.content or "{}"
            data = json.loads(response_content)

            # Validálás és kiegészítés alapértelmezésekkel
            category = data.get("category", raw_email.default_category)
            if category not in ["személyes", "munka", "egyetem", "projekt", "egyéb"]:
                category = raw_email.default_category

            urgency = data.get("urgency", "közepes")
            if urgency not in ["kritikus", "magas", "közepes", "alacsony"]:
                urgency = "közepes"

            importance = data.get("importance", "normál")
            if importance not in ["kiemelt", "normál", "alacsony"]:
                importance = "normál"

            summary = data.get("summary") or f"{raw_email.sender}: {raw_email.subject}"
            action_items = data.get("action_items") if isinstance(data.get("action_items"), list) else []
            deadlines = data.get("deadlines") if isinstance(data.get("deadlines"), list) else []

            return EmailAnalysis(
                category=category,
                urgency=urgency,
                importance=importance,
                summary=summary,
                action_items=[str(item) for item in action_items if item],
                deadlines=[str(dl) for dl in deadlines if dl],
            )
        except Exception as e:
            print(f"[WARN] Hiba a Groq elemzés során ({raw_email.subject}): {e}")
            return EmailAnalysis(
                category=raw_email.default_category,
                urgency="közepes",
                importance="normál",
                summary=f"{raw_email.sender}: {raw_email.subject}",
                action_items=[],
                deadlines=[],
            )

    def generate_daily_digest(self, processed_emails: List[ProcessedEmail]) -> str:
        """Összeállít egy tömör, Pushbullet-kompatibilis napi összefoglalót."""
        if not processed_emails:
            return "📬 Ma nem érkezett új feldolgozandó email a figyelt fiókokba."

        urgent_items: List[str] = []
        action_items: List[str] = []
        deadlines: List[str] = []
        by_category: dict[str, List[ProcessedEmail]] = {}

        for item in processed_emails:
            cat = item.analysis.category
            by_category.setdefault(cat, []).append(item)

            if item.analysis.urgency in ["kritikus", "magas"]:
                urgent_items.append(
                    f"• [{item.analysis.urgency.upper()}] {item.raw.subject} ({item.raw.account_name})"
                )

            for act in item.analysis.action_items:
                action_items.append(f"• {act} (Levél: {item.raw.subject})")

            for dl in item.analysis.deadlines:
                deadlines.append(f"• {dl} (Levél: {item.raw.subject})")

        lines: List[str] = []
        lines.append(f"📬 Napi Email Összesítő ({len(processed_emails)} új levél)")
        lines.append("=" * 30)

        if urgent_items:
            lines.append("\n🚨 SÜRGŐS / FONTOS:")
            lines.extend(urgent_items)

        if deadlines:
            lines.append("\n📅 HATÁRIDŐK:")
            lines.extend(deadlines)

        if action_items:
            lines.append("\n✅ TEENDŐK:")
            lines.extend(action_items[:8])  # Pushbullet limit miatt ésszerű keret
            if len(action_items) > 8:
                lines.append(f"  ...és további {len(action_items) - 8} teendő.")

        lines.append("\n📁 KATEGÓRIÁK SZERINT:")
        for cat, emails in by_category.items():
            lines.append(f"\n[{cat.upper()}] ({len(emails)} levél):")
            for mail in emails[:3]:
                lines.append(f"- {mail.raw.subject}: {mail.analysis.summary}")
            if len(emails) > 3:
                lines.append(f"  (+{len(emails) - 3} további)")

        return "\n".join(lines)
