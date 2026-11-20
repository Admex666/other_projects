from __future__ import annotations

from enum import Enum
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator


class EventCategory(str, Enum):
    MUSIC = "music"
    PARTY_NIGHTLIFE = "party_nightlife"
    GASTRONOMY = "gastronomy"
    CULTURE_ARTS = "culture_arts"
    COMMUNITY_FESTIVAL = "community_festival"
    SPORTS_WELLNESS = "sports_wellness"
    OTHER = "other"


class EventConfidence(str, Enum):
    VERIFIED_API = "verified_api"           # 1.0 - Hivatalos API kulccsal hitelesített forrás
    SCRAPED_STRUCTURED = "scraped_structured" # 0.85 - Schema.org JSON-LD / Nyílt GraphQL
    COMMUNITY_CURATED = "community_curated" # 0.70 - Turisztikai naptár / RSS / Agenda
    LOW_CONFIDENCE = "low_confidence"       # 0.40 - Hiányos vagy nem megerősített adat


class EventStatus(str, Enum):
    CONFIRMED = "confirmed"
    SCHEDULED = "scheduled"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class EventVenue(BaseModel):
    name: str = Field(..., description="A helyszín vagy klub neve")
    address: Optional[str] = Field(None, description="A helyszín pontos címe")
    city: str = Field(..., description="Város neve")
    country: Optional[str] = Field(None, description="Ország neve")
    latitude: Optional[float] = Field(None, description="Szélességi koordináta")
    longitude: Optional[float] = Field(None, description="Hosszúsági koordináta")


class EventItem(BaseModel):
    id: str = Field(..., description="Egyedi esemény azonosító (pl. ev_eb_12345 vagy ev_ra_987)")
    title: str = Field(..., min_length=2, description="Az esemény hivatalos címe")
    description: Optional[str] = Field(None, description="Rövid leírás vagy felvezető szöveg")
    city: str = Field(..., description="Célváros (pl. Barcelona, Malaga, Valencia)")
    venue: Optional[EventVenue] = Field(None, description="Rendezvény helyszíne")
    
    start_datetime: datetime = Field(..., description="Kezdés pontos dátuma és ideje (ISO)")
    end_datetime: Optional[datetime] = Field(None, description="Vége pontos dátuma és ideje (ISO)")
    
    category: EventCategory = Field(EventCategory.OTHER, description="Esemény kategóriája")
    tags: List[str] = Field(default_factory=list, description="Keresési és stílus címkék (pl. nye, techno, tapas)")
    
    price_min: Optional[float] = Field(None, description="Minimum jegyár vagy belépő (ha ismert)")
    price_max: Optional[float] = Field(None, description="Maximum jegyár vagy belépő (ha ismert)")
    currency: Optional[str] = Field("EUR", description="Pénznem (alapértelmezetten EUR)")
    is_free: Optional[bool] = Field(False, description="Ingyenes-e az esemény")
    
    source: str = Field(..., description="Forrás megnevezése (eventbrite, resident_advisor, ticketmaster, local_agenda)")
    source_url: str = Field(..., description="Közvetlen ellenőrizhető forrás link (ADR-004)")
    image_url: Optional[str] = Field(None, description="Promóciós kép vagy szórólap URL-je")
    
    confidence: EventConfidence = Field(EventConfidence.SCRAPED_STRUCTURED, description="Megbízhatósági szint")
    confidence_score: float = Field(0.85, ge=0.0, le=1.0, description="Numerikus megbízhatósági pontszám (0.0 - 1.0)")
    status: EventStatus = Field(EventStatus.CONFIRMED, description="Esemény státusza")
    
    is_nye_relevant: bool = Field(False, description="Szilveszteri időszakhoz (dec 31 - jan 1) kapcsolódik-e")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Event title cannot be empty")
        return clean

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("source_url must be a valid HTTP/HTTPS URL (ADR-004 Honest Scraping)")
        return v


class EventQuery(BaseModel):
    city: str = Field(..., description="Célváros neve (pl. Alicante, Malaga, Valencia, Barcelona, Sevilla, Catania, Valletta, Paphos, Lisbon)")
    start_date: date = Field(..., description="Kezdő dátum (pl. 2026-12-28)")
    end_date: date = Field(..., description="Záró dátum (pl. 2027-01-03)")
    categories: Optional[List[EventCategory]] = Field(None, description="Kategória szűrő")
    is_nye_only: bool = Field(False, description="Kizárólag szilveszteri/újévi események")
    min_confidence_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimális megbízhatósági küszöbérték")
    limit_per_category: int = Field(15, ge=1, le=100, description="Maximális találat kategóriánként")


class CategoryEventSummary(BaseModel):
    category: EventCategory
    count: int
    events: List[EventItem]


class EventSearchResult(BaseModel):
    city: str
    query_start_date: date
    query_end_date: date
    total_events: int
    categories: Dict[str, CategoryEventSummary]
    sources_used: List[str]
    honest_validation_passed: bool = Field(True, description="Minden elem megfelelt az ADR-004 Honest Scraping szűrőknek")
    errors_or_warnings: List[str] = Field(default_factory=list)
