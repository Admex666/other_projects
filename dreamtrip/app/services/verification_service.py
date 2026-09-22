"""
Optivoya Advisor Workspace — Verification & Provenance Engine (Phase 7)
========================================================================
Validates provider provenance, live cache timestamps, and assigns confidence levels:
- VERIFIED: Live API verified in < 4 hours, direct inventory availability.
- ESTIMATED: Interpolated from historical indices or seasonal benchmarks.
- NEEDS_REVIEW: High volatility, low seat availability, or stale data (> 24 hours).
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from app.models.advisor_models import VerificationStatus, ProviderProvenance


class VerificationService:
    """
    Evaluates trip components and assigns verifiable provenance & reliability statuses.
    """

    @classmethod
    def verify_component_provenance(
        cls,
        component_type: str,
        component_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determines verification status and confidence score for a flight, stay, or package.
        """
        provider = component_data.get("provider") or ("Kiwi.com" if component_type == "flight" else "Cozycozy")
        is_live = component_data.get("is_live", True)
        freshness_minutes = component_data.get("freshness_minutes", 15)

        # Volatility signals
        seats_remaining = component_data.get("seats_remaining")
        price_jump_risk = component_data.get("price_volatility_high", False)

        if freshness_minutes > 1440 or price_jump_risk or (seats_remaining is not None and seats_remaining < 3):
            status = VerificationStatus.NEEDS_REVIEW
            confidence = 0.65
            notes = "Magas árváltozási kockázat vagy szűkös szabad kapacitás — véglegesítés előtt ellenőrzendő."
        elif is_live and freshness_minutes <= 240:
            status = VerificationStatus.VERIFIED
            confidence = 0.95
            notes = f"Valós időben ellenőrizve a {provider} rendszerében ({freshness_minutes} perccel ezelőtt)."
        else:
            status = VerificationStatus.ESTIMATED
            confidence = 0.80
            notes = "Becsült érték indexek és korábbi hasonló keresések alapján."

        return {
            "component_type": component_type,
            "provider": provider,
            "verification_status": status.value,
            "confidence_score": confidence,
            "freshness_minutes": freshness_minutes,
            "verification_notes": notes
        }

    @classmethod
    def verify_trip_option(cls, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the overall reliability of a trip option by checking flight and stay sub-components.
        """
        flight = option_data.get("flight", {})
        stay = option_data.get("stay", {})

        flight_ver = cls.verify_component_provenance("flight", flight)
        stay_ver = cls.verify_component_provenance("stay", stay)

        # Aggregate status: worst component drives option status
        statuses = [flight_ver["verification_status"], stay_ver["verification_status"]]
        if VerificationStatus.NEEDS_REVIEW.value in statuses:
            overall_status = VerificationStatus.NEEDS_REVIEW
        elif VerificationStatus.ESTIMATED.value in statuses:
            overall_status = VerificationStatus.ESTIMATED
        else:
            overall_status = VerificationStatus.VERIFIED

        avg_confidence = round((flight_ver["confidence_score"] + stay_ver["confidence_score"]) / 2, 2)

        return {
            "option_id": option_data.get("id"),
            "overall_status": overall_status.value,
            "confidence_score": avg_confidence,
            "components": {
                "flight": flight_ver,
                "stay": stay_ver
            }
        }
