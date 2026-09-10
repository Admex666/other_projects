"""Alapvető absztrakt osztály az adatforrás-gyűjtőkhöz és forrás-validációhoz."""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Tuple
import httpx

from quizforge.core.config import settings
from quizforge.core.constants import SourceType
from quizforge.core.models import Entity, Relation, SourceValidationReport


class BaseIngestor(ABC):
    """Adatforrás-gyűjtő alaposztály."""

    def __init__(self, source_name: str, source_type: SourceType, endpoint: str):
        self.source_name = source_name
        self.source_type = source_type
        self.endpoint = endpoint
        self.client = httpx.Client(
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": settings.USER_AGENT},
            follow_redirects=True
        )

    @abstractmethod
    def fetch_sample(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Próbagyűjtés futtatása a forrásból."""
        pass

    @abstractmethod
    def extract_triplets(self, sample_data: List[Dict[str, Any]]) -> Tuple[List[Entity], List[Relation]]:
        """Knowledge Graph entitások és relációk kinyerése a mintaadatokból."""
        pass

    def validate_source(self, limit: int = 5) -> SourceValidationReport:
        """Teszteli az elérhetőséget, válaszidőt, és a kinyerhető adatok minőségét."""
        start_time = time.time()
        report = SourceValidationReport(
            source_name=self.source_name,
            source_type=self.source_type,
            endpoint=self.endpoint,
            is_accessible=False,
            response_time_ms=0.0,
            records_fetched=0,
            sample_records=[],
            schema_compliance=False,
            kg_suitability_score=0.0,
            notes=""
        )

        try:
            records = self.fetch_sample(limit=limit)
            elapsed = (time.time() - start_time) * 1000.0
            report.response_time_ms = round(elapsed, 2)
            report.records_fetched = len(records)
            report.sample_records = records[:3]
            report.is_accessible = True

            # Próbálunk tripleteket kinyerni az alkalmasság tesztelésére
            entities, relations = self.extract_triplets(records)
            if records and (len(entities) > 0 or len(relations) > 0):
                report.schema_compliance = True
                # Alkalmassági pontszám arányos az entitások/relációk gazdagságával
                suitability = min(1.0, (len(entities) + len(relations) * 2) / (max(len(records), 1) * 3))
                report.kg_suitability_score = round(suitability, 2)
                report.notes = f"Sikeres adatkinyerés: {len(entities)} entitás, {len(relations)} reláció generálva a mintából."
            else:
                report.notes = "Az adatok letölthetők, de a strukturált KG kinyeréséhez további átalakítás szükséges."

        except httpx.HTTPStatusError as e:
            report.response_time_ms = round((time.time() - start_time) * 1000.0, 2)
            report.status_code = e.response.status_code
            report.error_message = f"HTTP hiba: {e.response.status_code} - {str(e)}"
        except Exception as e:
            report.response_time_ms = round((time.time() - start_time) * 1000.0, 2)
            report.error_message = f"Váratlan hiba a lekérdezés során: {str(e)}"

        return report

    def close(self):
        self.client.close()
