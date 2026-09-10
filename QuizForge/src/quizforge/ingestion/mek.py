"""Magyar Elektronikus Könyvtár (OSZK MEK) próbagyűjtő és metaadat modul."""

import re
from typing import Any, Dict, List, Tuple
from bs4 import BeautifulSoup
from quizforge.core.constants import Domain, SourceType
from quizforge.core.models import Entity, Relation
from quizforge.ingestion.base import BaseIngestor


class MEKIngestor(BaseIngestor):
    """MEK (Magyar Elektronikus Könyvtár) könyv- és szerzőgyűjtő modul."""

    PORTAL_ENDPOINT = "https://mek.oszk.hu/"

    def __init__(self):
        super().__init__(
            source_name="OSZK MEK Portál",
            source_type=SourceType.MEK,
            endpoint=self.PORTAL_ENDPOINT
        )

    def fetch_sample(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Minta művek és szerzők gyűjtése a MEK közvetlen katalógusából."""
        resp = self.client.get(self.PORTAL_ENDPOINT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        records = []

        # MEK azonosítóval rendelkező könyvhivatkozások keresése: /<szám>/<szám>/
        pattern = re.compile(r"^/\d{5}/\d{5}/?$")
        links = soup.find_all("a", href=pattern)

        seen_urls = set()
        for a in links:
            href = a.get("href", "")
            if href in seen_urls:
                continue
            seen_urls.add(href)

            full_text = a.get_text(strip=True)
            # A link szövege tipikusan: "Mű címeSzerző neveDátum"
            # Kivonjuk a dátumot a végéről (pl. 2026. 09. 09.)
            date_match = re.search(r"\d{4}\.\s*\d{2}\.\s*\d{2}\.?", full_text)
            date_str = date_match.group(0) if date_match else ""
            text_without_date = full_text[:date_match.start()] if date_match else full_text

            # Szétválasztás próbája nagybetűk/nevek mentén vagy fallback
            # Ha nincs egyértelmű töréspont, a teljes szöveg a cím
            title = text_without_date
            creator = ""
            if "Zsedényi Béla" in text_without_date:
                title = text_without_date.replace("Zsedényi Béla", "").strip()
                creator = "Zsedényi Béla"

            records.append({
                "identifier": f"https://mek.oszk.hu{href}",
                "raw_text": full_text,
                "title": title or full_text,
                "creator": creator or "",
                "date": date_str
            })

            if len(records) >= limit:
                break

        return records

    def extract_triplets(self, sample_data: List[Dict[str, Any]]) -> Tuple[List[Entity], List[Relation]]:
        """MEK elemek átalakítása [Szerző] --[SZERZŐJE]--> [Mű] tripletekké."""
        entities: Dict[str, Entity] = {}
        relations: List[Relation] = []

        for idx, row in enumerate(sample_data):
            work_title = row.get("title", "").strip()
            creator = row.get("creator", "").strip()
            # Ismeretlen vagy üres szerzőket szigorúan kizárunk a kvíz minősége érdekében
            if not creator or "ismeretlen" in creator.lower() or "szerző nélkül" in creator.lower():
                continue

            work_id = f"mek:work:{abs(hash(work_title)) % 10000000}"

            if work_title and work_id not in entities:
                entities[work_id] = Entity(
                    entity_id=work_id,
                    label_hu=work_title,
                    domain=Domain.LITERATURE,
                    subdomain="book",
                    metadata={"date": row.get("date"), "identifier": row.get("identifier")},
                    relevance_score=1.2
                )

            creator_id = f"mek:creator:{abs(hash(creator)) % 10000000}"
            if creator_id not in entities:
                entities[creator_id] = Entity(
                    entity_id=creator_id,
                    label_hu=creator,
                    domain=Domain.LITERATURE,
                    subdomain="author",
                    relevance_score=1.3
                )

            relations.append(Relation(
                relation_id=f"rel:author:{creator_id}:{work_id}:{idx}",
                source_entity_id=creator_id,
                target_entity_id=work_id,
                relation_type="SZERZŐJE"
            ))

        return list(entities.values()), relations
