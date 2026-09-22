"""
Optivoya Advisor Workspace — Timeline & Re-Optimization Service (Phase 9)
========================================================================
Manages client feedback recording, audit timeline event logging,
and 1-click re-optimization workflows producing branched proposals (v2, v3).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.advisor_models import (
    TripCase, Client, TripCaseStatus, ResolvedTripPreferences,
    HardConstraints, SoftPreferences, generate_uuid, utc_now
)
from app.services.multi_option_engine import MultiOptionEngine
from app.services.proposal_service import ProposalService
from app.services.preference_resolver import PreferenceResolver


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{generate_uuid()[:8]}")
    case_id: str
    event_type: str # CASE_CREATED, BRIEF_RECORDED, RESEARCH_EXECUTED, PROPOSAL_CREATED, CLIENT_FEEDBACK, REOPTIMIZED, CASE_CLOSED
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TimelineReoptimizationService:
    """
    Handles event logging, feedback tracking, and automated re-optimization pipelines.
    """

    _TIMELINE_STORE: Dict[str, List[Dict[str, Any]]] = {}
    _FEEDBACK_STORE: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def log_event(
        cls,
        case_id: str,
        event_type: str,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Logs a timestamped audit event to the case timeline.
        """
        if case_id not in cls._TIMELINE_STORE:
            cls._TIMELINE_STORE[case_id] = []

        event = {
            "id": f"evt_{generate_uuid()[:8]}",
            "case_id": case_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "metadata": metadata or {},
            "created_at": utc_now().isoformat()
        }

        cls._TIMELINE_STORE[case_id].append(event)
        return event

    @classmethod
    def get_case_timeline(cls, case_id: str) -> List[Dict[str, Any]]:
        """
        Returns chronological timeline events for a case, most recent first.
        """
        events = cls._TIMELINE_STORE.get(case_id, [])
        return sorted(events, key=lambda x: x.get("created_at", ""), reverse=True)

    @classmethod
    def record_feedback(
        cls,
        case_id: str,
        proposal_id: str,
        feedback_category: str, # e.g. "budget_too_high", "hotel_upgrade", "flight_timing", "general"
        feedback_text: str,
        client_sentiment: str = "NEUTRAL" # POSITIVE, NEUTRAL, CRITICAL
    ) -> Dict[str, Any]:
        """
        Records structured client feedback against a specific proposal version.
        """
        if case_id not in cls._FEEDBACK_STORE:
            cls._FEEDBACK_STORE[case_id] = []

        feedback_record = {
            "id": f"fb_{generate_uuid()[:8]}",
            "case_id": case_id,
            "proposal_id": proposal_id,
            "feedback_category": feedback_category,
            "feedback_text": feedback_text,
            "client_sentiment": client_sentiment,
            "created_at": utc_now().isoformat()
        }
        cls._FEEDBACK_STORE[case_id].append(feedback_record)

        # Log timeline event
        cls.log_event(
            case_id=case_id,
            event_type="CLIENT_FEEDBACK",
            title=f"Ügyfél Visszajelzés Rögzítve ({feedback_category})",
            description=feedback_text,
            metadata={"proposal_id": proposal_id, "sentiment": client_sentiment}
        )

        return feedback_record

    @classmethod
    def execute_reoptimization(
        cls,
        trip_case: TripCase,
        client: Client,
        base_proposal: Dict[str, Any],
        candidates_pool: List[Dict[str, Any]],
        constraint_overrides: Optional[Dict[str, Any]] = None,
        reoptimization_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        1-Click Re-Optimization:
        1. Applies modifications to constraints (e.g. lower budget, direct flights only, higher star hotel).
        2. Re-runs MultiOptionEngine archetypes on the candidate pool.
        3. Creates Proposal v(N+1) snapshot branched from base_proposal.
        4. Logs REOPTIMIZATION and PROPOSAL_VERSION timeline events.
        """
        # Apply constraint overrides if provided
        if constraint_overrides:
            if "total_budget_huf" in constraint_overrides:
                trip_case.total_budget_huf = float(constraint_overrides["total_budget_huf"])

            if trip_case.preferences and trip_case.preferences.hard:
                for k, v in constraint_overrides.items():
                    if hasattr(trip_case.preferences.hard, k):
                        setattr(trip_case.preferences.hard, k, v)

        # Resolve preferences
        resolved = PreferenceResolver.resolve_preferences(trip_case, client)

        # Re-generate archetypes
        new_options = MultiOptionEngine.generate_archetypes(
            candidates=candidates_pool,
            preferences=resolved,
            target_budget_huf=trip_case.total_budget_huf
        )

        # Create next proposal version
        reason_text = reoptimization_reason or "Ügyfél visszajelzés alapján módosított preferenciák"
        new_proposal = ProposalService.create_next_version(
            base_proposal=base_proposal,
            updated_options=new_options,
            reason=reason_text
        )

        # Update case status
        trip_case.status = TripCaseStatus.PROPOSAL
        trip_case.updated_at = utc_now()

        # Log timeline events
        cls.log_event(
            case_id=trip_case.id,
            event_type="REOPTIMIZATION_EXECUTED",
            title=f"Újragenerálás Sikeresen Lefutott (v{new_proposal.get('version', 2)})",
            description=f"Ok: {reason_text}. Generált opciók: {len(new_options)} db.",
            metadata={"new_proposal_id": new_proposal.get("id"), "options_count": len(new_options)}
        )

        return {
            "status": "success",
            "case_id": trip_case.id,
            "new_proposal": new_proposal,
            "new_options": new_options,
            "version": new_proposal.get("version", 2)
        }
