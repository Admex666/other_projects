"""
Wikipedia Knowledge & Description Connector
Extracts authentic cultural narratives, historical summaries, and thumbnail images.
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseConnector, DestinationSeed, RawSourceRecord

WIKIPEDIA_REST_BASE = "https://en.wikipedia.org/api/rest_v1"

class WikipediaConnector(BaseConnector):
    def __init__(self, parser_version: str = "v1.0", timeout_sec: int = 15):
        super().__init__(name="wikipedia", license_name="CC-BY-SA 4.0", parser_version=parser_version)
        self.timeout_sec = timeout_sec

    def fetch_records(self, seed: DestinationSeed, limit: int = 10) -> List[RawSourceRecord]:
        records: List[RawSourceRecord] = []
        now_iso = datetime.utcnow().isoformat()
        headers = {
            "User-Agent": "OptivoyaExperienceEngine/1.0 (https://optivoya.com; info@optivoya.com)",
            "Accept": "application/json"
        }

        # 1. Fetch main destination city overview
        city_slug = seed.name.replace(" ", "_")
        try:
            url = f"{WIKIPEDIA_REST_BASE}/page/summary/{city_slug}"
            resp = requests.get(url, headers=headers, timeout=self.timeout_sec)
            if resp.status_code == 200:
                payload = resp.json()
                page_id = str(payload.get("pageid", city_slug))
                records.append(RawSourceRecord(
                    source=self.name,
                    source_id=page_id,
                    destination_id=seed.destination_id,
                    name_candidate=payload.get("title", seed.name),
                    raw_payload=payload,
                    license=self.license_name,
                    retrieved_at=now_iso,
                    parser_version=self.parser_version
                ))
        except Exception as e:
            print(f"[WIKIPEDIA CONNECTOR WARN] Main summary failed for {city_slug}: {e}")

        # 2. Fetch coordinate-based landmark / attraction articles via official Wikipedia Geosearch API
        try:
            radius_m = min(int(seed.radius_km * 1000), 10000)
            geo_url = f"https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{seed.lat}|{seed.lon}",
                "gsradius": radius_m,
                "gslimit": limit,
                "format": "json"
            }
            resp = requests.get(geo_url, params=params, headers=headers, timeout=self.timeout_sec)
            if resp.status_code == 200:
                geo_results = resp.json().get("query", {}).get("geosearch", [])
                for item in geo_results:
                    title = item.get("title")
                    page_id = str(item.get("pageid"))
                    if not title or title.lower() == seed.name.lower():
                        continue

                    # Fetch summary for each landmark candidate
                    try:
                        sum_url = f"{WIKIPEDIA_REST_BASE}/page/summary/{title.replace(' ', '_')}"
                        s_resp = requests.get(sum_url, headers=headers, timeout=5)
                        if s_resp.status_code == 200:
                            s_data = s_resp.json()
                            s_data["dist_meters"] = item.get("dist")
                            records.append(RawSourceRecord(
                                source=self.name,
                                source_id=page_id,
                                destination_id=seed.destination_id,
                                name_candidate=s_data.get("title", title),
                                raw_payload=s_data,
                                license=self.license_name,
                                retrieved_at=now_iso,
                                parser_version=self.parser_version
                            ))
                    except Exception:
                        pass
        except Exception as e:
            print(f"[WIKIPEDIA GEOSEARCH WARN] Geosearch query failed: {e}")

        return records
