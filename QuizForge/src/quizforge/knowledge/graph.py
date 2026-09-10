"""Knowledge Graph építő és disztraktor-választó modul."""

import random
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import Domain
from quizforge.core.models import Entity, Relation
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import EntityRepository, RelationRepository


class KnowledgeGraph:
    """A központi tudásgráf kezelő réteg."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.entities = EntityRepository(db)
        self.relations = RelationRepository(db)

    def ingest_triplets(self, entities: List[Entity], relations: List[Relation]) -> Tuple[int, int]:
        """Új entitások és relációk betöltése és deduplikálása."""
        added_entities = 0
        added_relations = 0

        for ent in entities:
            self.entities.upsert(ent)
            added_entities += 1

        for rel in relations:
            self.relations.upsert(rel)
            added_relations += 1

        return added_entities, added_relations

    def get_distractors(
        self,
        correct_entity_id: str,
        correct_label: Optional[str] = None,
        domain: Optional[Domain] = None,
        subdomain: Optional[str] = None,
        count: int = 3
    ) -> List[str]:
        """
        Determinisztikus, intelligens disztraktorok (hibás válaszok) kinyerése a gráfból.
        A helyes válasszal azonos domainből és subdomaintípussal rendelkező entitások közül választ,
        kizárva az ismeretlen/junk elemeket és a helyes válasz kisbetűs/nagybetűs változatait.
        """
        # Ha nincs átadva correct_label, lekérdezzük
        if not correct_label:
            correct_ent = self.entities.get_by_id(correct_entity_id)
            correct_label = correct_ent.label_hu.strip() if correct_ent else ""
            if not domain and correct_ent:
                domain = correct_ent.domain
            if not subdomain and correct_ent:
                subdomain = correct_ent.subdomain

        target_domain = domain.value if isinstance(domain, Domain) else (domain or "general_knowledge")
        target_subdomain = subdomain
        clean_correct = correct_label.strip()

        # 1. Próbálkozás: szigorú subdomain és domain egyezés (kizárva kategóriákat, ismeretleneket)
        query = """
            SELECT DISTINCT label_hu FROM entities
            WHERE entity_id != ? 
              AND entity_id NOT LIKE 'wiki:cat:%'
              AND subdomain NOT LIKE '%category%'
              AND label_hu NOT ILIKE '%Ismeretlen%'
              AND label_hu NOT ILIKE '%MEK szerző%'
              AND label_hu NOT ILIKE '%szerző nélkül%'
              AND label_hu NOT ILIKE '%Zsedényi%'
              AND LOWER(label_hu) != LOWER(?)
        """
        params = [correct_entity_id, clean_correct]

        if target_subdomain:
            query += " AND subdomain = ?"
            params.append(target_subdomain)
        elif target_domain:
            query += " AND domain = ?"
            params.append(target_domain)

        query += " ORDER BY relevance_score DESC LIMIT ?"
        params.append(count * 6)

        rows = self.db.conn.execute(query, params).fetchall()
        candidate_distractors = [r[0].strip() for r in rows if r[0] and r[0].strip()]

        # 2. Ha a szigorú subdomain egyezéssel nincs meg a kellő számú disztraktor (< count),
        # csak akkor lazítunk témakör (domain) szintre
        if len(candidate_distractors) < count and target_subdomain:
            fallback_query = """
                SELECT DISTINCT label_hu FROM entities
                WHERE entity_id != ?
                  AND entity_id NOT LIKE 'wiki:cat:%'
                  AND subdomain NOT LIKE '%category%'
                  AND label_hu NOT ILIKE '%Ismeretlen%'
                  AND label_hu NOT ILIKE '%MEK szerző%'
                  AND label_hu NOT ILIKE '%szerző nélkül%'
                  AND label_hu NOT ILIKE '%Zsedényi%'
                  AND domain = ?
                  AND LOWER(label_hu) != LOWER(?)
                ORDER BY relevance_score DESC LIMIT ?
            """
            fallback_rows = self.db.conn.execute(
                fallback_query,
                [correct_entity_id, target_domain, clean_correct, count * 3]
            ).fetchall()
            candidate_distractors.extend([r[0].strip() for r in fallback_rows if r[0] and r[0].strip()])

        # 3. Szigorú Case-Insensitive Deduplikáció és Keverés
        random.shuffle(candidate_distractors)
        seen_lower = {clean_correct.lower()}
        distractors = []

        for item in candidate_distractors:
            item_clean = item.strip()
            if not item_clean:
                continue
            item_lower = item_clean.lower()
            if item_lower not in seen_lower:
                seen_lower.add(item_lower)
                # Formázás: nagy kezdőbetű az opciókhoz az egységességért
                formatted_item = item_clean[0].upper() + item_clean[1:] if len(item_clean) > 1 else item_clean.upper()
                distractors.append(formatted_item)
            if len(distractors) == count:
                break

        return distractors
