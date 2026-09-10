"""Automatikus kvízkérdés-generáló pipeline a Knowledge Graph adatai alapján."""

import random
from typing import Any, Dict, List, Optional
from quizforge.core.constants import Domain, QuestionMechanism, SourceType
from quizforge.core.models import Entity, RawQuizQuestion, Relation
from quizforge.knowledge.graph import KnowledgeGraph
from quizforge.llm.groq_client import GroqClient
from quizforge.quiz_engine.mechanisms.abcd import ABCDMechanism
from quizforge.quiz_engine.mechanisms.connection import ConnectionMechanism
from quizforge.quiz_engine.mechanisms.estimation import EstimationMechanism
from quizforge.quiz_engine.mechanisms.matching import MatchingMechanism
from quizforge.quiz_engine.mechanisms.ordering import OrderingMechanism
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import QuizQuestionRepository


class QuizGenerator:
    """Tudásgráfból többféle mechanizmussal kérdéseket generáló motor."""

    def __init__(self, db: DatabaseManager, groq_client: Optional[GroqClient] = None):
        self.db = db
        self.kg = KnowledgeGraph(db)
        self.groq = groq_client or GroqClient()
        self.question_repo = QuizQuestionRepository(db)

        # Mechanizmus regiszter
        self.mechanisms = {
            QuestionMechanism.ABCD: ABCDMechanism(),
            QuestionMechanism.ESTIMATION: EstimationMechanism(),
            QuestionMechanism.ORDERING: OrderingMechanism(),
            QuestionMechanism.MATCHING: MatchingMechanism(),
            QuestionMechanism.CONNECTION: ConnectionMechanism(),
        }

    def generate_question(
        self,
        domain: Optional[Domain] = None,
        preferred_mechanism: Optional[QuestionMechanism] = None,
        exclude_entity_ids: Optional[set] = None
    ) -> Optional[RawQuizQuestion]:
        """Egy új kvízkérdés generálása a gráfból deduplikációval és szigorú szemantikával."""
        excluded = exclude_entity_ids or set()

        # 1. Triplet választás a gráfból:
        # KIZÁRJUK a gyűjtőkategóriákat, a MEK jogi cikkeket és a már felhasznált entitásokat!
        query = """
            SELECT r.relation_id, r.relation_type, r.metadata,
                   e_src.entity_id, e_src.label_hu, e_src.domain, e_src.subdomain, e_src.relevance_score,
                   e_tgt.entity_id, e_tgt.label_hu, e_tgt.domain, e_tgt.subdomain, e_tgt.relevance_score
            FROM relations r
            JOIN entities e_src ON r.source_entity_id = e_src.entity_id
            JOIN entities e_tgt ON r.target_entity_id = e_tgt.entity_id
            WHERE r.relation_type != 'KATEGÓRIÁJA'
              AND e_tgt.entity_id NOT LIKE 'wiki:cat:%'
              AND e_src.entity_id NOT LIKE 'mek:%'
              AND e_tgt.entity_id NOT LIKE 'mek:%'
              AND e_src.label_hu NOT LIKE '%Ismeretlen%'
              AND e_tgt.label_hu NOT LIKE '%Ismeretlen%'
              AND (e_tgt.subdomain IS NULL OR e_tgt.subdomain NOT LIKE '%category%')
              AND (e_src.subdomain IS NULL OR e_src.subdomain NOT LIKE '%category%')
        """
        params = []
        if domain:
            query += " AND (e_src.domain = ? OR e_tgt.domain = ?)"
            params.extend([domain.value, domain.value])

        if excluded:
            ex_list = list(excluded)
            placeholders = ','.join(['?'] * len(ex_list))
            query += f" AND e_src.entity_id NOT IN ({placeholders}) AND e_tgt.entity_id NOT IN ({placeholders})"
            params.extend(ex_list)
            params.extend(ex_list)

        # Véletlenszerű kiválasztás a releváns kapcsolatok közül
        query += " ORDER BY RANDOM() LIMIT 1"

        row = self.db.conn.execute(query, params).fetchone()
        if not row:
            # Ha a szigorú kizárással elfogytak, fallback kizárás nélkül
            if excluded:
                return self.generate_question(domain=domain, preferred_mechanism=preferred_mechanism, exclude_entity_ids=None)
            return None

        rel_meta = row[2] if isinstance(row[2], dict) else {}
        src = Entity(entity_id=row[3], label_hu=row[4], domain=Domain(row[5]), subdomain=row[6])
        tgt = Entity(entity_id=row[8], label_hu=row[9], domain=Domain(row[10]), subdomain=row[11])
        rel = Relation(relation_id=row[0], source_entity_id=row[3], target_entity_id=row[8], relation_type=row[1], metadata=rel_meta)

        # 2. Mechanizmus kiválasztása
        mechanism = preferred_mechanism
        if not mechanism:
            if "year" in rel.metadata and rel.metadata["year"]:
                mechanism = QuestionMechanism.ESTIMATION
            else:
                mechanism = QuestionMechanism.ABCD

        # 3. Kérdés irány és disztraktorok előkészítése
        # ask_target=True: a célpont (tgt) a helyes válasz. ask_target=False: az alany (src) a helyes válasz.
        ask_target = True
        custom_question = ""
        prompt_instruction = ""

        if rel.relation_type == "KAPOTT_DÍJAT":
            ask_target = True
            custom_question = f"Milyen Nobel-díjat kapott {src.label_hu}?"
            prompt_instruction = f"A kérdésnek arra kell rákérdeznie, hogy {src.label_hu} milyen Nobel-díjat kapott. A helyes válasz: {tgt.label_hu}."
        elif rel.relation_type == "SZÉKHELYE":
            ask_target = True
            custom_question = f"Mi {src.label_hu} székhelye?"
            prompt_instruction = f"A kérdésnek arra kell rákérdeznie, hogy mi {src.label_hu} székhelye. A helyes válasz: {tgt.label_hu}."
        elif rel.relation_type == "TALÁLMÁNYA":
            ask_target = True
            custom_question = f"Melyik híres magyar találmány fűződik {src.label_hu} nevéhez?"
            prompt_instruction = f"A kérdésnek arra kell rákérdeznie, hogy melyik találmány fűződik {src.label_hu} nevéhez. A helyes válasz: {tgt.label_hu}."
        elif rel.relation_type == "SZERZŐJE":
            # 50% eséllyel a művet, 50% eséllyel a szerzőt kérdezzük meg
            if random.random() < 0.5:
                ask_target = True  # A művet kérdezzük (tgt = book)
                custom_question = f"Melyik híres magyar mű szerzője {src.label_hu}?"
                prompt_instruction = f"A kérdésnek arra kell rákérdeznie, hogy {src.label_hu} melyik híres magyar művet írta. A helyes válasz: {tgt.label_hu}."
            else:
                ask_target = False  # A szerzőt kérdezzük (src = author)
                custom_question = f"Ki írta a(z) '{tgt.label_hu}' című művet?"
                prompt_instruction = f"A kérdésnek arra kell rákérdeznie, hogy ki írta a(z) '{tgt.label_hu}' című művet. A helyes válasz: {src.label_hu}."

        if mechanism == QuestionMechanism.ESTIMATION and "year" in rel.metadata:
            correct_val = str(rel.metadata["year"])
            question_text = f"Melyik évben kapott {tgt.label_hu} elismerést {src.label_hu}?"
            options = []
            final_domain = src.domain
            final_subdomain = src.subdomain
        else:
            if ask_target:
                target_ent = tgt
                subject_ent = src
            else:
                target_ent = src
                subject_ent = tgt

            raw_label = target_ent.label_hu.strip()
            # Egységes, szép kezdőbetű formázás (pl. golyóstoll -> Golyóstoll)
            correct_val = raw_label[0].upper() + raw_label[1:] if len(raw_label) > 1 else raw_label.upper()
            target_entity_for_llm = target_ent
            subject_entity_for_llm = subject_ent
            final_domain = target_ent.domain
            final_subdomain = target_ent.subdomain

            distractors = self.kg.get_distractors(
                target_ent.entity_id,
                correct_label=correct_val,
                domain=target_ent.domain,
                subdomain=target_ent.subdomain,
                count=3
            )

            # Szigorú opció deduplikáció
            options = [correct_val]
            seen_options_lower = {correct_val.lower()}
            for d in distractors:
                d_clean = d.strip()
                if not d_clean:
                    continue
                d_norm = d_clean[0].upper() + d_clean[1:] if len(d_clean) > 1 else d_clean.upper()
                if d_norm.lower() not in seen_options_lower:
                    seen_options_lower.add(d_norm.lower())
                    options.append(d_norm)

            # Ha véletlenül 4-nél kevesebb egyedi opció maradt, töltsük fel azonos témájú elemekkel
            if len(options) < 4:
                filler_query = """
                    SELECT DISTINCT label_hu FROM entities
                    WHERE entity_id != ?
                      AND label_hu NOT ILIKE '%Ismeretlen%'
                      AND label_hu NOT ILIKE '%MEK szerző%'
                      AND label_hu NOT ILIKE '%szerző nélkül%'
                      AND subdomain NOT LIKE '%category%'
                      AND domain = ?
                    LIMIT 15
                """
                fillers = self.db.conn.execute(filler_query, [target_ent.entity_id, final_domain.value]).fetchall()
                for f in fillers:
                    f_name = f[0].strip()
                    f_norm = f_name[0].upper() + f_name[1:] if len(f_name) > 1 else f_name.upper()
                    if f_norm.lower() not in seen_options_lower:
                        seen_options_lower.add(f_norm.lower())
                        options.append(f_norm)
                    if len(options) == 4:
                        break

            random.shuffle(options)

            # LLM megfogalmazás futtatása a kristálytiszta instrukcióval
            if self.groq.is_available:
                llm_res = self.groq.formulate_question_from_triplet(
                    source_entity=subject_entity_for_llm,
                    relation=rel,
                    target_entity=target_entity_for_llm,
                    mechanism=mechanism,
                    distractors=distractors,
                    custom_instruction=prompt_instruction
                )
                question_text = llm_res.get("question_text", "")
            else:
                question_text = ""

            # Determinisztikus fallback, ha a Groq üres vagy nem illeszkedik
            if not question_text or "kategóri" in question_text.lower():
                question_text = custom_question or f"Mi igaz a következőre: {src.label_hu}?"

        # 4. Kérdés létrehozása és tárolása
        q_id = f"gen:{src.entity_id}:{tgt.entity_id}:{random.randint(1000, 9999)}"
        new_q = RawQuizQuestion(
            question_id=q_id,
            text=question_text,
            mechanism=mechanism,
            correct_answer=correct_val,
            options=options,
            domain=final_domain,
            subdomain=final_subdomain,
            source_type=SourceType.WIKIDATA,
            source_name="QuizForge KG Generator",
            entities=[src.entity_id, tgt.entity_id],
            metadata={"relation_type": rel.relation_type}
        )

        if not getattr(self.db, "read_only", False):
            self.question_repo.add_question(new_q)
        return new_q

    def generate_batch(self, count: int = 5, domain: Optional[Domain] = None) -> List[RawQuizQuestion]:
        """Több kérdés kötegelt generálása ismétlődések nélkül, témák körforgásával."""
        generated = []
        used_entity_ids = set()

        # Ha nincs téma megadva, ciklikusan váltogatjuk a fő témákat
        available_domains = [Domain.SCIENCE_TECH, Domain.GEOGRAPHY, Domain.LITERATURE]
        
        for i in range(count):
            current_domain = domain or available_domains[i % len(available_domains)]
            q = self.generate_question(domain=current_domain, exclude_entity_ids=used_entity_ids)
            if q:
                generated.append(q)
                for ent_id in q.entities:
                    used_entity_ids.add(ent_id)
        return generated
