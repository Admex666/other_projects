"""
Base Connector Interface for Optivoya Experience Ingestion Pipeline
Guarantees strict source provenance, raw data preservation, and unified error handling.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class DestinationSeed:
    destination_id: str   # e.g. "IT_BARI"
    name: str             # "Bari"
    country: str          # "Italy"
    lat: float            # 41.1171
    lon: float            # 16.8719
    radius_km: float = 15.0 # scope radius in km

@dataclass
class RawSourceRecord:
    source: str               # "osm", "wikidata", "wikipedia", "google_maps"
    source_id: str            # Unique ID in source (e.g. node/12345, Q3519, place_id)
    destination_id: str       # "IT_BARI"
    name_candidate: str       # Extracted name string
    raw_payload: Dict[str, Any] # Complete unmodified json from source
    license: str              # e.g. "ODbL", "CC-0", "CC-BY-SA 4.0", "Proprietary"
    retrieved_at: str         # ISO timestamp
    parser_version: str = "v1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseConnector(ABC):
    """Abstract base connector for external geospatial, semantic, and commercial sources."""

    def __init__(self, name: str, license_name: str, parser_version: str = "v1.0"):
        self.name = name
        self.license_name = license_name
        self.parser_version = parser_version

    @abstractmethod
    def fetch_records(self, seed: DestinationSeed, limit: int = 50) -> List[RawSourceRecord]:
        """Fetches raw source records for a destination seed."""
        pass
