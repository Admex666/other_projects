"""
Wikidata Semantic Connector
Extracts structured semantic entities, cultural heritage classifications, and Wikipedia cross-links.
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseConnector, DestinationSeed, RawSourceRecord

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

class WikidataConnector(BaseConnector):
    def __init__(self, parser_version: str = "v1.0", timeout_sec: int = 25):
        super().__init__(name="wikidata", license_name="CC-0", parser_version=parser_version)
        self.timeout_sec = timeout_sec

    def fetch_records(self, seed: DestinationSeed, limit: int = 50) -> List[RawSourceRecord]:
        # SPARQL query retrieving cultural landmarks, museums, beaches, and historic points around coordinate
        query = f"""
        SELECT ?place ?placeLabel ?location ?instanceOf ?instanceOfLabel ?wikipedia ?image WHERE {{
          SERVICE wikibase:around {{
            ?place wdt:P625 ?location .
            bd:serviceParam wikibase:center "Point({seed.lon} {seed.lat})"^^geo:wktLiteral .
            bd:serviceParam wikibase:radius "{seed.radius_km}" .
          }}
          ?place wdt:P31 ?instanceOf .
          OPTIONAL {{ ?place wdt:P18 ?image . }}
          OPTIONAL {{
            ?wikipedia schema:about ?place ;
                       schema:isPartOf <https://en.wikipedia.org/> .
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en,hu" . }}
        }}
        LIMIT {limit}
        """

        headers = {
            "User-Agent": "OptivoyaExperienceEngine/1.0 (https://optivoya.com; travel data integration)",
            "Accept": "application/sparql-results+json"
        }

        try:
            resp = requests.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers=headers,
                timeout=self.timeout_sec
            )
            if resp.status_code == 200:
                data = resp.json()
                bindings = data.get("results", {}).get("bindings", [])
                records: List[RawSourceRecord] = []
                now_iso = datetime.utcnow().isoformat()

                for b in bindings:
                    uri = b.get("place", {}).get("value", "")
                    qid = uri.split("/")[-1] if "/" in uri else uri
                    lbl = b.get("placeLabel", {}).get("value", "")
                    
                    if not lbl or lbl == qid:
                        continue  # Skip unlabelled items

                    # Flatten raw payload
                    payload = {
                        "qid": qid,
                        "label": lbl,
                        "instance_of": b.get("instanceOf", {}).get("value", ""),
                        "instance_of_label": b.get("instanceOfLabel", {}).get("value", ""),
                        "location_wkt": b.get("location", {}).get("value", ""),
                        "wikipedia_url": b.get("wikipedia", {}).get("value"),
                        "image_url": b.get("image", {}).get("value")
                    }

                    records.append(RawSourceRecord(
                        source=self.name,
                        source_id=qid,
                        destination_id=seed.destination_id,
                        name_candidate=lbl,
                        raw_payload=payload,
                        license=self.license_name,
                        retrieved_at=now_iso,
                        parser_version=self.parser_version
                    ))

                return records
            else:
                print(f"[WIKIDATA CONNECTOR WARN] Returned status {resp.status_code}")
        except Exception as e:
            print(f"[WIKIDATA CONNECTOR ERROR] {e}")

        return []
