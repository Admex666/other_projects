"""Groq LLM kliens kérdésmegfogalmazáshoz és nyers kérdések strukturálásához."""

import json
from typing import Any, Dict, List, Optional
from quizforge.core.config import settings
from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.core.models import Entity, Relation


class GroqClient:
    """
    Groq API integráció a gyors, költséghatékony kérdésszövegezéshez.
    SZABÁLY: Az LLM nem 'találhat ki' tényeket, kizárólag a kapott KG adatokból fogalmazhat!
    Folyamatosan naplózza a rendelkezésre álló tokeneket és request kvótát.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self._client = None
        self.last_quota: Dict[str, Any] = {}

        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None and bool(self.api_key)

    def get_quota_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Lekéri a valós idejű GROQ API token- és kéréskvótát a hivatalos response fejlécekből.
        Ha force_refresh=True vagy még nincs mentett adat, egy minimális (1 tokenes) kéréssel frissíti.
        """
        if not self.is_available:
            return {"available": False, "message": "GROQ API nem elérhető (hiányzó kulcs)."}

        if force_refresh or not self.last_quota or not self.last_quota.get("remaining_tokens"):
            try:
                from datetime import datetime
                raw_res = self._client.chat.completions.with_raw_response.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1
                )
                headers = raw_res.headers
                self.last_quota = {
                    "available": True,
                    "remaining_tokens": headers.get("x-ratelimit-remaining-tokens"),
                    "limit_tokens": headers.get("x-ratelimit-limit-tokens"),
                    "remaining_requests": headers.get("x-ratelimit-remaining-requests"),
                    "limit_requests": headers.get("x-ratelimit-limit-requests"),
                    "reset_tokens": headers.get("x-ratelimit-reset-tokens"),
                    "reset_requests": headers.get("x-ratelimit-reset-requests"),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                self.last_quota["error"] = str(e)

        return self.last_quota

    def format_quota_summary(self, force_refresh: bool = False) -> str:
        """Emberileg jól olvasható kvóta összefoglaló a CLI-hez és UI-hoz."""
        q = self.get_quota_status(force_refresh=force_refresh)
        if not q.get("available"):
            return "[Groq API] Nem elérhető vagy offline."
        
        rem_tok = q.get("remaining_tokens", "?")
        lim_tok = q.get("limit_tokens", "?")
        rem_req = q.get("remaining_requests", "?")
        lim_req = q.get("limit_requests", "?")
        res_tok = q.get("reset_tokens", "?")
        res_req = q.get("reset_requests", "?")
        
        return (
            f"[Groq API Kvóta] Tokenek: {rem_tok} / {lim_tok} (Reset: {res_tok}) | "
            f"Kérések: {rem_req} / {lim_req} (Reset: {res_req})"
        )

    def formulate_question_from_triplet(
        self,
        source_entity: Entity,
        relation: Relation,
        target_entity: Entity,
        mechanism: QuestionMechanism = QuestionMechanism.ABCD,
        distractors: Optional[List[str]] = None,
        custom_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kérdésszöveg megfogalmazása a Knowledge Graph triplet alapján.
        """
        if not self.is_available:
            return {
                "question_text": custom_instruction or f"Mi a kapcsolata: {source_entity.label_hu} és {target_entity.label_hu}?",
                "correct_answer": target_entity.label_hu,
                "distractors": distractors or [],
                "mechanism": mechanism.value,
                "provider": "offline_fallback"
            }

        instruction_text = custom_instruction or f"A kérdésnek közvetlenül a következő tényre kell rákérdeznie: {source_entity.label_hu} ({relation.relation_type}: {target_entity.label_hu})."

        prompt = f"""Feladatod egy professzionális, természetes magyar pub quiz / trivia kérdés megfogalmazása a megadott tény alapján.

PONTOS CÉL:
{instruction_text}

SZIGORÚ SZABÁLYOK:
1. TILOS olyan kérdést feltenni, hogy "Melyik kategóriába tartozik / sorolható...?"!
2. A kérdés közvetlenül a kívánt tényre kérdezzen rá!
3. A kérdésszövegbe NE írd bele a választási opciókat vagy A), B), C), D) betűket, csak magát a tiszta kérdésmondatot!
4. TILOS új tényeket kitalálni! A helyes válasz pontosan: "{target_entity.label_hu}".

Megadott tényadatok:
- Alany: {source_entity.label_hu}
- Kapcsolat: {relation.relation_type}
- Helyes válasz: {target_entity.label_hu}
- Alternatív lehetőségek: {', '.join(distractors) if distractors else 'N/A'}

Válaszolj KIZÁRÓLAG érvényes JSON formátumban:
{{
  "question_text": "A tiszta kérdés szövege kérdőjellel a végén",
  "correct_answer": "{target_entity.label_hu}",
  "explanation": "1 mondatos rövid magyarázat"
}}"""

        # Raw response kérése a rate limit és token fejlécek kinyeréséhez
        raw_res = self._client.chat.completions.with_raw_response.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Te egy tapasztalt magyar kvízmester vagy, aki életszerű, izgalmas kocsmakvíz kérdéseket fogalmaz meg. Szigorúan érvényes JSON-ben válaszolsz."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        # Kvóta és token információk kimentése a response fejlécekből
        headers = raw_res.headers
        parsed_completion = raw_res.parse()

        from datetime import datetime
        self.last_quota = {
            "available": True,
            "remaining_tokens": headers.get("x-ratelimit-remaining-tokens"),
            "limit_tokens": headers.get("x-ratelimit-limit-tokens"),
            "remaining_requests": headers.get("x-ratelimit-remaining-requests"),
            "limit_requests": headers.get("x-ratelimit-limit-requests"),
            "reset_tokens": headers.get("x-ratelimit-reset-tokens"),
            "reset_requests": headers.get("x-ratelimit-reset-requests"),
            "prompt_tokens": getattr(parsed_completion.usage, "prompt_tokens", None),
            "completion_tokens": getattr(parsed_completion.usage, "completion_tokens", None),
            "total_tokens": getattr(parsed_completion.usage, "total_tokens", None),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        content = parsed_completion.choices[0].message.content.strip()
        # Ha a modell markdown kódblokkba csomagolta a JSON-t:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(content)
        except Exception:
            data = {
                "question_text": f"Milyen díjat kapott {source_entity.label_hu}?",
                "correct_answer": target_entity.label_hu,
                "raw_response": content
            }

        data["distractors"] = distractors or []
        data["mechanism"] = mechanism.value
        data["provider"] = f"groq:{self.model}"
        data["quota"] = self.last_quota
        return data

    def extract_entities_from_raw_question(self, question_text: str) -> Dict[str, Any]:
        """
        Nyers beérkező kérdésből entitások, kategóriák és mechanizmus automatikus kinyerése.
        """
        if not self.is_available:
            return {
                "detected_domain": Domain.GENERAL_KNOWLEDGE.value,
                "detected_mechanism": QuestionMechanism.ABCD.value,
                "entities": [],
                "provider": "offline_fallback"
            }

        prompt = f"""Elemezd az alábbi magyar kvízkérdést és nyerd ki belőle a kulcsfontosságú entitásokat, a várható témakört és a kérdésmechanizmust!

Kérdés: "{question_text}"

Válaszolj KIZÁRÓLAG érvényes JSON formátumban:
{{
  "domain": "history / geography / literature / science_tech / pop_culture / sports / art_music / gastronomy / general",
  "subdomain": "pl. nobel / cities / prime_ministers",
  "mechanism": "abcd / estimation / ordering / matching / connection / true_false",
  "entities": ["Entitás 1", "Entitás 2"]
}}"""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Te egy kvíz- és tudásgráf elemző AI vagy. Csak szigorúan érvényes JSON-ben válaszolsz."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        data["provider"] = f"groq:{self.model}"
        return data
