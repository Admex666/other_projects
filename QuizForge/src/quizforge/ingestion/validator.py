"""Adatforrás-validátor és mintagyűjtés-futtató pipeline."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from quizforge.core.config import settings
from quizforge.core.models import SourceValidationReport
from quizforge.ingestion.base import BaseIngestor
from quizforge.ingestion.mek import MEKIngestor
from quizforge.ingestion.quiz_sources import HungarianPubQuizSampleCorpus, OpenTriviaIngestor
from quizforge.ingestion.wikidata import WikidataIngestor
from quizforge.ingestion.wikipedia import WikipediaIngestor


class SourceValidationPipeline:
    """Minden regisztrált adatforrás próbagyűjtését és validációját koordináló osztály."""

    def __init__(self):
        self.ingestors: List[BaseIngestor] = [
            WikidataIngestor(),
            WikipediaIngestor(),
            MEKIngestor(),
            OpenTriviaIngestor(),
        ]

    def run_validation(self, sample_limit: int = 5) -> Dict[str, Any]:
        reports: List[SourceValidationReport] = []
        raw_samples: Dict[str, Any] = {}

        print("=" * 60)
        print("QuizForge - 1. Fázis: Adatforrás Validáció és Próbagyűjtés")
        print("=" * 60)

        for ingestor in self.ingestors:
            print(f"--> Tesztelés alatt: {ingestor.source_name} ({ingestor.endpoint})...")
            report = ingestor.validate_source(limit=sample_limit)
            reports.append(report)

            status_str = "SIKERES" if report.is_accessible else "HIBA"
            print(f"    Állapot: [{status_str}] | Válaszidő: {report.response_time_ms} ms | Rekordok: {report.records_fetched}")
            if report.error_message:
                print(f"    Hiba: {report.error_message}")
            if report.notes:
                print(f"    Info: {report.notes}")

            # Nyers minta mentése
            raw_samples[ingestor.source_name] = {
                "report": report.model_dump(),
                "sample_records": report.sample_records
            }
            ingestor.close()

        # Magyar mintakorpusz hozzáadása
        seed_questions = HungarianPubQuizSampleCorpus.get_seed_questions()
        raw_samples["Hungarian Pub Quiz Seed Corpus"] = [q.model_dump() for q in seed_questions]
        print(f"--> Magyar Pub Quiz seed korpusz: {len(seed_questions)} minta kérdés előkészítve.")

        # Fájlok mentése a data/raw alá
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_output_path = settings.RAW_DATA_DIR / f"validation_report_{timestamp}.json"
        latest_json_path = settings.RAW_DATA_DIR / "source_validation_report.json"
        
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(raw_samples, f, ensure_ascii=False, indent=2, default=str)
        with open(latest_json_path, "w", encoding="utf-8") as f:
            json.dump(raw_samples, f, ensure_ascii=False, indent=2, default=str)

        # Markdown összefoglaló generálása
        md_summary = self._generate_markdown_summary(reports, len(seed_questions), json_output_path)
        md_output_path = settings.RAW_DATA_DIR / "source_validation_report.md"
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(md_summary)

        print("\n" + "=" * 60)
        print(f"Validációs jelentés elmentve ide: {latest_json_path}")
        print(f"Markdown összefoglaló: {md_output_path}")
        print("=" * 60)

        return {
            "reports": [r.model_dump() for r in reports],
            "report_path_json": str(latest_json_path),
            "report_path_md": str(md_output_path)
        }

    def _generate_markdown_summary(
        self,
        reports: List[SourceValidationReport],
        seed_count: int,
        json_path: Path
    ) -> str:
        lines = [
            "# QuizForge - 1. Fázis: Adatforrás Validációs Jelentés",
            f"\n*Generálva: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*",
            f"\n*Nyers adatok helye: `{json_path.name}`*\n",
            "## 1. Források Összehasonlítása",
            "",
            "| Forrás Neve | Típus | Elérhető | Válaszidő (ms) | Rekordok | KG Alkalmasság | Megjegyzés |",
            "|---|---|:---:|:---:|:---:|:---:|---|"
        ]

        for r in reports:
            acc_emoji = "✅" if r.is_accessible else "❌"
            lines.append(
                f"| **{r.source_name}** | `{r.source_type.value}` | {acc_emoji} | {r.response_time_ms} | "
                f"{r.records_fetched} | {int(r.kg_suitability_score * 100)}% | {r.notes or r.error_message or '-'} |"
            )

        lines.extend([
            "",
            "## 2. Kvízkorpusz Tesztkészlet",
            f"- **Magyar Pub Quiz Seed Korpusz:** {seed_count} különböző mechanizmusú kérdés definiálva (ABCD, Becslés, Sorrend, Párosítás, Kapcsolat).",
            "",
            "## 3. Következtetések és Javasolt Következő Lépések",
            "1. **Wikidata SPARQL:** Kiemelkedően alkalmas közvetlen Knowledge Graph tripletek kinyerésére (személyek, helyek, díjak, évszámok).",
            "2. **Magyar Wikipédia:** Kiválóan alkalmas kategóriafák és kontextuális leírások/kivonatok gyűjtésére.",
            "3. **OSZK MEK:** Magyar kulturális, szépirodalmi és történelmi művek/szerzők gazdag forrása.",
            "4. **Kvízkorpusz:** A mechanizmus-sémák készen állnak a DuckDB tárolásra és a kérdésgenerátor illesztésére."
        ])

        return "\n".join(lines)


if __name__ == "__main__":
    pipeline = SourceValidationPipeline()
    pipeline.run_validation(sample_limit=5)
