"""
Data models for Optivoya Experience & Activity Intelligence Engine.
Maps 1:1 to Supabase PostgreSQL experience tables.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class CanonicalExperienceEntity:
    entity_id: str
    destination_id: str
    canonical_name: str
    category: str
    subcategory: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    rating: Optional[float] = None
    review_count: int = 0
    price_level: str = "moderate"
    est_duration_hours: float = 1.5
    best_time_of_day: str = "anytime"
    confidence_score: float = 1.0
    sources_present: List[str] = field(default_factory=list)
    source_ids: Dict[str, str] = field(default_factory=dict)
    image_urls: List[str] = field(default_factory=list)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DestinationExperienceProfile:
    destination_id: str
    city_name: str
    country: str
    total_activities_count: int = 0
    category_distribution: Dict[str, int] = field(default_factory=dict)
    top_experiences_summary: List[Dict[str, Any]] = field(default_factory=list)
    vibe_scores: Dict[str, float] = field(default_factory=dict)
    confidence_level: float = 1.0
    last_synced_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
