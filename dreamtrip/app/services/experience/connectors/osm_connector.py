"""
OpenStreetMap (OSM) Overpass Connector
Extracts raw geospatial and amenity/tourism records without rate limiting issues.
"""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseConnector, DestinationSeed, RawSourceRecord

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

class OSMConnector(BaseConnector):
    def __init__(self, parser_version: str = "v1.0", timeout_sec: int = 25):
        super().__init__(name="osm", license_name="ODbL", parser_version=parser_version)
        self.timeout_sec = timeout_sec

    def fetch_records(self, seed: DestinationSeed, limit: int = 50) -> List[RawSourceRecord]:
        # Convert radius to approximate bounding box for fast spatial index execution
        import math
        d_lat = seed.radius_km / 111.0
        d_lon = seed.radius_km / (111.0 * math.cos(math.radians(seed.lat)))
        min_lat = round(seed.lat - d_lat, 4)
        max_lat = round(seed.lat + d_lat, 4)
        min_lon = round(seed.lon - d_lon, 4)
        max_lon = round(seed.lon + d_lon, 4)
        bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        # Overpass QL query targeted at travel experiences (attractions, beaches, culture, nature, promenades)
        query = f"""[out:json][timeout:{self.timeout_sec}];
(
  node["tourism"~"attraction|viewpoint|museum|gallery|theme_park|artwork|zoo|aquarium|picnic_site"]({bbox_str});
  way["tourism"~"attraction|viewpoint|museum|gallery|theme_park|artwork|zoo|aquarium"]({bbox_str});
  node["natural"~"beach|peak|cave_entrance|cliff|water|bay|cape"]({bbox_str});
  way["natural"~"beach|water"]({bbox_str});
  node["historic"~"monument|castle|ruins|archaeological_site|church|cathedral|memorial|city_gate|fort|heritage"]({bbox_str});
  way["historic"~"castle|monument|ruins|archaeological_site|fort"]({bbox_str});
  node["leisure"~"park|nature_reserve|garden|marina|water_park"]({bbox_str});
  way["leisure"~"park|nature_reserve|garden|marina"]({bbox_str});
  node["amenity"~"theatre|arts_centre|marketplace|fountain"]({bbox_str});
);
out center tags {limit};"""

        headers = {
            "User-Agent": "OptivoyaExperienceEngine/1.0 (https://optivoya.com; travel intelligence)",
            "Accept": "application/json"
        }

        for endpoint in OVERPASS_ENDPOINTS:
            try:
                resp = requests.post(
                    endpoint,
                    data={"data": query},
                    headers=headers,
                    timeout=self.timeout_sec
                )
                if resp.status_code == 200:
                    data = resp.json()
                    elements = data.get("elements", [])
                    records: List[RawSourceRecord] = []
                    now_iso = datetime.utcnow().isoformat()

                    for el in elements:
                        tags = el.get("tags", {})
                        name = tags.get("name") or tags.get("name:en") or tags.get("name:it")
                        if not name:
                            continue  # Skip unnamed nodes

                        el_type = el.get("type", "node")
                        el_id = el.get("id")
                        source_id = f"{el_type}/{el_id}"

                        records.append(RawSourceRecord(
                            source=self.name,
                            source_id=source_id,
                            destination_id=seed.destination_id,
                            name_candidate=name,
                            raw_payload=el,
                            license=self.license_name,
                            retrieved_at=now_iso,
                            parser_version=self.parser_version
                        ))

                    return records
            except Exception as e:
                print(f"[OSM CONNECTOR WARN] Overpass endpoint {endpoint} failed: {e}")

        return []
