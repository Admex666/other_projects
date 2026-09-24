"""
Optivoya Shared Intelligence — Hierarchical Preference Resolver
Resolves multi-layered client and advisor preferences into a concrete, executable specification.

Hierarchy Resolution Chain:
  Layer 4: Advisor Overrides (Pinned items, forced direct flights, manual markup)
     ↓
  Layer 3: Case Brief (Trip-specific budget ceilings, dates, party size, custom constraints)
     ↓
  Layer 2: Client Profile (Persistent travel style, airline preferences, min stars/rating)
     ↓
  Layer 1: System Defaults (Fallbacks for unconstrained fields)
"""

from typing import Optional, Dict, Any
from app.models.advisor_models import (
    TripCase, Client, ClientPreferences,
    HardConstraints, SoftPreferences, AvoidRules, NiceToHave,
    AdvisorOverrides, ResolvedTripPreferences, BudgetMode
)


class PreferenceResolver:
    """
    Deterministic hierarchical resolver combining persistent client profiles,
    trip-specific brief specifications, and manual advisor overrides.
    """

    @classmethod
    def resolve_preferences(
        cls,
        trip_case: TripCase,
        client: Optional[Client] = None,
        advisor_overrides: Optional[AdvisorOverrides] = None
    ) -> ResolvedTripPreferences:
        """
        Resolves the 4-layer preference hierarchy for a TripCase.
        """
        # 1. Base Defaults (Layer 1)
        hard = HardConstraints(
            direct_flights_only=False,
            max_stops=1,
            min_hotel_stars=3,
            min_hotel_rating=7.5,
            min_safety_score=50
        )
        soft = SoftPreferences()
        avoid = AvoidRules()
        nice = NiceToHave()
        overrides = advisor_overrides or trip_case.preferences.overrides or AdvisorOverrides()

        # 2. Apply Client Profile (Layer 2)
        if client and client.preferences:
            cp: ClientPreferences = client.preferences
            if cp.hotel_min_stars is not None:
                hard.min_hotel_stars = cp.hotel_min_stars
            if cp.hotel_min_rating is not None:
                hard.min_hotel_rating = cp.hotel_min_rating
            if cp.direct_flights_only is not None:
                hard.direct_flights_only = cp.direct_flights_only
            if cp.max_stops is not None:
                hard.max_stops = cp.max_stops
            if cp.avoid_airlines:
                avoid.avoid_airlines = list(cp.avoid_airlines)
            if cp.interests:
                for interest in cp.interests:
                    soft.vibe_weights[interest] = 80.0

        # 3. Apply Case Brief (Layer 3)
        cb_prefs = trip_case.preferences
        if cb_prefs:
            # Merge Hard constraints
            if cb_prefs.hard:
                cb_h = cb_prefs.hard
                if cb_h.max_total_budget_huf is not None:
                    hard.max_total_budget_huf = cb_h.max_total_budget_huf
                if cb_h.max_flight_budget_huf is not None:
                    hard.max_flight_budget_huf = cb_h.max_flight_budget_huf
                if cb_h.max_stay_budget_huf is not None:
                    hard.max_stay_budget_huf = cb_h.max_stay_budget_huf
                if cb_h.direct_flights_only is not None:
                    hard.direct_flights_only = cb_h.direct_flights_only
                if cb_h.max_stops is not None:
                    hard.max_stops = cb_h.max_stops
                if cb_h.min_hotel_stars is not None:
                    hard.min_hotel_stars = cb_h.min_hotel_stars
                if cb_h.min_hotel_rating is not None:
                    hard.min_hotel_rating = cb_h.min_hotel_rating
                if cb_h.min_safety_score is not None:
                    hard.min_safety_score = cb_h.min_safety_score

            # Merge Soft preferences (if customized)
            if cb_prefs.soft:
                cb_s = cb_prefs.soft
                if cb_s.target_temperature is not None:
                    soft.target_temperature = cb_s.target_temperature
                if cb_s.budget_flexibility_pct is not None:
                    soft.budget_flexibility_pct = cb_s.budget_flexibility_pct
                # Only overwrite specific custom vibes if brief has custom non-empty dict differing from standard defaults
                for k, v in cb_s.vibe_weights.items():
                    if k in soft.vibe_weights and v != 50.0:  # custom value in brief
                        soft.vibe_weights[k] = v

            # Merge Avoid rules
            if cb_prefs.avoid:
                cb_a = cb_prefs.avoid
                avoid.avoid_airlines = list(set(avoid.avoid_airlines + cb_a.avoid_airlines))
                avoid.avoid_early_departures = cb_a.avoid_early_departures
                avoid.avoid_late_arrivals = cb_a.avoid_late_arrivals
                avoid.avoid_destinations = list(set(avoid.avoid_destinations + cb_a.avoid_destinations))
                avoid.avoid_hotel_types = list(set(avoid.avoid_hotel_types + cb_a.avoid_hotel_types))

            # Merge Nice to have
            if cb_prefs.nice_to_have:
                cb_n = cb_prefs.nice_to_have
                nice.breakfast_included = cb_n.breakfast_included
                nice.pool_available = cb_n.pool_available
                nice.sea_view = cb_n.sea_view
                nice.free_cancellation = cb_n.free_cancellation
                nice.central_location = cb_n.central_location

        # Apply Case direct budget only if strictly configured as HARD
        if hasattr(trip_case, "budget_constraint") and trip_case.budget_constraint:
            if hasattr(trip_case.budget_constraint, "total") and getattr(trip_case.budget_constraint.total, "hardness", "") == "hard":
                hard.max_total_budget_huf = trip_case.budget_constraint.total.amount
        elif trip_case.preferences and trip_case.preferences.hard and trip_case.preferences.hard.max_total_budget_huf is not None:
            hard.max_total_budget_huf = trip_case.preferences.hard.max_total_budget_huf

        # 4. Apply Advisor Overrides (Layer 4)
        if overrides:
            if overrides.pinned_destination:
                trip_case.destination_focus = overrides.pinned_destination

        return ResolvedTripPreferences(
            hard=hard,
            soft=soft,
            avoid=avoid,
            nice_to_have=nice,
            overrides=overrides
        )

    @classmethod
    def validate_budget_mode(cls, trip_case: TripCase) -> Dict[str, Any]:
        """
        Validates the consistency of the budget configuration based on the active BudgetMode.
        """
        mode = trip_case.budget_mode
        hard = trip_case.preferences.hard

        if mode == BudgetMode.TOTAL_BUDGET:
            budget = trip_case.total_budget_huf or (hard.max_total_budget_huf if hard else None)
            if not budget or budget <= 0:
                return {"valid": False, "error": "Total budget ceiling is required for Mode A (Total Budget)."}
            return {"valid": True, "mode": "total", "total_budget_huf": budget}

        elif mode == BudgetMode.COMPONENT_BUDGETS:
            f_budget = trip_case.flight_budget_huf or (hard.max_flight_budget_huf if hard else None)
            s_budget = trip_case.stay_budget_huf or (hard.max_stay_budget_huf if hard else None)
            if not f_budget and not s_budget:
                return {"valid": False, "error": "At least one component budget (flight or stay) must be specified for Mode B."}
            return {"valid": True, "mode": "component", "flight_budget_huf": f_budget, "stay_budget_huf": s_budget}

        elif mode == BudgetMode.SCOPE_ONLY:
            return {"valid": True, "mode": "scope_only", "note": "Unconstrained value-optimized search."}

        return {"valid": True, "mode": str(mode)}
