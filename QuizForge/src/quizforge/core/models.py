"""Adatmodellek a QuizForge entitásokhoz, kapcsolatokhoz és kérdésekhez."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from quizforge.core.constants import Domain, QuestionMechanism, SourceType


class Entity(BaseModel):
    """Knowledge Graph entitás (személy, hely, esemény, fogalom stb.)."""
    entity_id: str = Field(description="Egyedi azonosító (pl. wd:Q12345 vagy auto slug)")
    label_hu: str = Field(description="Magyar megnevezés")
    label_en: Optional[str] = None
    domain: Domain = Domain.GENERAL_KNOWLEDGE
    subdomain: Optional[str] = None
    wikidata_qid: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = Field(default=1.0, description="Kezdeti relevancia súly")


class Relation(BaseModel):
    """Két entitás közötti irányított kapcsolat (triplet)."""
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str = Field(description="Reláció típusa (pl. SZÜLETETT_HELYE, DÍJAT_KAPOTT, SZERZŐJE)")
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RawQuizQuestion(BaseModel):
    """Nyers vagy gyűjtött kvízkérdés."""
    question_id: str
    text: str
    mechanism: QuestionMechanism = QuestionMechanism.ABCD
    correct_answer: str
    options: List[str] = Field(default_factory=list)
    domain: Domain = Domain.GENERAL_KNOWLEDGE
    subdomain: Optional[str] = None
    source_type: SourceType = SourceType.OPEN_TRIVIA
    source_name: str
    entities: List[str] = Field(default_factory=list, description="Kérdésben szereplő entitások azonosítói")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceValidationReport(BaseModel):
    """Egy adott adatforrás próbatesztjének eredménye."""
    source_name: str
    source_type: SourceType
    endpoint: str
    is_accessible: bool
    status_code: Optional[int] = None
    response_time_ms: float
    records_fetched: int
    sample_records: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    schema_compliance: bool = False
    kg_suitability_score: float = Field(
        default=0.0,
        description="Mennyire alkalmas közvetlenül Knowledge Graph tripletek kinyerésére (0.0 - 1.0)"
    )
    notes: str = ""
