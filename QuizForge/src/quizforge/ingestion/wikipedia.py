"""Magyar Wikipédia API adatgyűjtő és kategória-elemző modul."""

from typing import Any, Dict, List, Tuple
from quizforge.core.constants import Domain, SourceType
from quizforge.core.models import Entity, Relation
from quizforge.ingestion.base import BaseIngestor


class WikipediaIngestor(BaseIngestor):
    """Magyar Wikipédia API kliens kategóriák és szócikk-kivonatok gyűjtésére."""

    API_ENDPOINT = "https://hu.wikipedia.org/w/api.php"

    def __init__(self):
        super().__init__(
            source_name="Magyar Wikipédia API",
            source_type=SourceType.WIKIPEDIA,
            endpoint=self.API_ENDPOINT
        )

    def fetch_sample(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Mintagyűjtés: Magyar találmányok kategória tagjai és kivonatai."""
        category_title = "Kategória:Magyar_találmányok"
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": limit,
            "cmtype": "page",
            "format": "json"
        }
        resp = self.client.get(self.API_ENDPOINT, params=params)
        resp.raise_for_status()
        members = resp.json().get("query", {}).get("categorymembers", [])
        
        page_ids = [str(m["pageid"]) for m in members if "pageid" in m]
        if not page_ids:
            return []

        # Részletes kivonatok (extracts) lekérése
        extract_params = {
            "action": "query",
            "pageids": "|".join(page_ids),
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "format": "json"
        }
        ext_resp = self.client.get(self.API_ENDPOINT, params=extract_params)
        ext_resp.raise_for_status()
        pages = ext_resp.json().get("query", {}).get("pages", {})

        results = []
        for pid, page in pages.items():
            results.append({
                "pageid": pid,
                "title": page.get("title", ""),
                "extract": page.get("extract", "")[:300],  # Első 300 karakter
                "fullurl": page.get("fullurl", ""),
                "category": category_title
            })
        return results

    def extract_triplets(self, sample_data: List[Dict[str, Any]]) -> Tuple[List[Entity], List[Relation]]:
        """Wikipédia szócikkek és kategóriák átalakítása entitásokká."""
        entities: List[Entity] = []
        relations: List[Relation] = []

        category_entity_id = "wiki:cat:magyar_talalmanyok"
        entities.append(Entity(
            entity_id=category_entity_id,
            label_hu="Magyar találmányok",
            domain=Domain.SCIENCE_TECH,
            subdomain="invention_category",
            relevance_score=1.5
        ))

        for row in sample_data:
            ent_id = f"wiki:page:{row.get('pageid')}"
            title = row.get("title", "")
            extract = row.get("extract", "")

            entities.append(Entity(
                entity_id=ent_id,
                label_hu=title,
                domain=Domain.SCIENCE_TECH,
                subdomain="invention",
                description=extract,
                metadata={"url": row.get("fullurl")},
                relevance_score=1.3
            ))

            relations.append(Relation(
                relation_id=f"rel:cat:{row.get('pageid')}",
                source_entity_id=ent_id,
                target_entity_id=category_entity_id,
                relation_type="KATEGÓRIÁJA"
            ))

        return entities, relations
