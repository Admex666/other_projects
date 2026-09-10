"""Célzott tanulási algoritmus: a személyes vakfoltok és a versenyprofil súlyozása."""

from typing import Any, Dict, List, Optional
from quizforge.core.models import RawQuizQuestion
from quizforge.optimizer.landscape import QuizLandscapeEngine, QuizProfile
from quizforge.player.repository import PlayerRepository
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import QuizQuestionRepository


class TargetedLearningEngine:
    """
    Összeveti a játékos képességmátrixát egy célzott kvízprofil követelményeivel,
    és kiválasztja a legnagyobb felkészülési haszonnal járó kérdéseket.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.landscape = QuizLandscapeEngine()
        self.player_repo = PlayerRepository(db)
        self.q_repo = QuizQuestionRepository(db)

    def get_player_skill_map(self, user_id: str) -> Dict[tuple, Dict[str, Any]]:
        """A játékos képességmátrixának átalakítása könnyen indexelhető szótárrá."""
        skills = self.player_repo.get_player_skills(user_id)
        skill_map = {}
        for s in skills:
            key = (s["domain"], s["mechanism"])
            skill_map[key] = s
        return skill_map

    def calculate_weak_spots(self, user_id: str, profile_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Kiszámítja, hogy egy adott kvízprofilon hol fog a játékos a legvalószínűbben pontokat veszíteni.
        Kockázati pontszám = ProfilSúly(domain) * ProfilSúly(mechanism) * (1 - SkillRating + OverconfidencePenalty)
        """
        profile = self.landscape.get_profile(profile_id)
        if not profile:
            return []

        skill_map = self.get_player_skill_map(user_id)
        risk_entries = []

        # Minden olyan (domain, mech) pár vizsgálata, ami a profilban szerepel
        for dom, dom_w in profile.domain_weights.items():
            for mech, mech_w in profile.mechanism_weights.items():
                skill_info = skill_map.get((dom, mech), {
                    "skill_rating": 0.5,  # Alapértelmezett ismeretlen szint
                    "confidence_bias": 0.0,
                    "sample_count": 0
                })

                skill_val = float(skill_info["skill_rating"])
                bias = float(skill_info["confidence_bias"])
                # Ha overconfident (többet képzel mint a valóság), az még kockázatosabb!
                penalty = max(0.0, bias) * 1.5

                # Kockázati index: minél nagyobb a kvízbeli súlya és minél kisebb a tudása, annál nagyobb
                risk_score = dom_w * mech_w * (1.1 - skill_val + penalty)

                risk_entries.append({
                    "domain": dom,
                    "mechanism": mech,
                    "profile_weight": round(dom_w * mech_w, 3),
                    "current_skill": round(skill_val, 2),
                    "confidence_bias": round(bias, 2),
                    "sample_count": skill_info["sample_count"],
                    "risk_score": round(risk_score, 4)
                })

        risk_entries.sort(key=lambda x: x["risk_score"], reverse=True)
        return risk_entries[:limit]

    def select_targeted_questions(
        self,
        user_id: str,
        profile_id: str,
        count: int = 5
    ) -> List[RawQuizQuestion]:
        """
        A profilhoz és a játékoshoz legjobban illeszkedő, legfontosabb fejlesztendő kérdések kiválasztása.
        """
        profile = self.landscape.get_profile(profile_id)
        if not profile:
            return []

        skill_map = self.get_player_skill_map(user_id)

        # Kérdések lekérdezése a DuckDB-ből
        rows = self.db.conn.execute("""
            SELECT question_id, text, mechanism, correct_answer, options, domain, subdomain, source_type, source_name, metadata
            FROM quiz_questions
        """).fetchall()

        if not rows:
            return []

        scored_questions = []
        for r in rows:
            q_dom = r[5]
            q_mech = r[2]

            dom_w = profile.get_domain_weight(q_dom)
            mech_w = profile.get_mechanism_weight(q_mech)

            # Ha a profil egyáltalán nem kéri ezt a témát vagy típust, alacsony prioritás
            if dom_w <= 0.02 and mech_w <= 0.02:
                priority = 0.01
            else:
                skill_info = skill_map.get((q_dom, q_mech), {
                    "skill_rating": 0.5,
                    "confidence_bias": 0.0
                })
                skill_val = float(skill_info["skill_rating"])
                bias = float(skill_info["confidence_bias"])
                penalty = max(0.0, bias) * 1.5

                # Prioritási formula
                priority = dom_w * mech_w * (1.2 - skill_val + penalty)

            scored_questions.append((priority, r))

        # Rendezés prioritás szerint csökkenő sorrendben
        scored_questions.sort(key=lambda x: x[0], reverse=True)

        selected = []
        import json
        from quizforge.core.constants import Domain, QuestionMechanism, SourceType

        for prio, r in scored_questions[:count]:
            selected.append(RawQuizQuestion(
                question_id=r[0],
                text=r[1],
                mechanism=QuestionMechanism(r[2]) if r[2] in [m.value for m in QuestionMechanism] else QuestionMechanism.ABCD,
                correct_answer=r[3],
                options=json.loads(r[4]) if r[4] else [],
                domain=Domain(r[5]) if r[5] in [d.value for d in Domain] else Domain.GENERAL_KNOWLEDGE,
                subdomain=r[6],
                source_type=SourceType(r[7]) if r[7] in [s.value for s in SourceType] else SourceType.MANUAL,
                source_name=r[8],
                metadata=json.loads(r[9]) if r[9] else {}
            ))

        return selected
