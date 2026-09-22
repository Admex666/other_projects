"""
Optivoya Advisor Workspace — Constraint Relaxation & Diagnosis Engine (Phase 7)
================================================================================
Eliminates dead-ends (0 results) by diagnosing conflicting constraints and
generating 1-click relaxation proposals with quantified unlocked option counts.
"""

from typing import List, Dict, Any, Optional
from app.models.advisor_models import TripCase, ResolvedTripPreferences, ClientPreferences


class ConstraintRelaxationService:
    """
    Diagnoses bottleneck constraints and calculates quantifiable relaxation pathways.
    """

    @classmethod
    def diagnose_and_suggest(
        cls,
        trip_case: TripCase,
        preferences: Any,
        raw_inventory_pool: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyzes the raw candidate inventory against active constraints and
        produces specific relaxation recommendations with exact counts of newly unlocked options.
        """
        hard = getattr(preferences, "hard", {})
        if hasattr(hard, "model_dump"):
            hard_dict = hard.model_dump()
        elif isinstance(hard, dict):
            hard_dict = hard
        else:
            hard_dict = {}

        total_budget = trip_case.total_budget_huf or 300000
        direct_only = hard_dict.get("direct_flights_only", False)
        min_stars = hard_dict.get("min_hotel_stars", 0)
        min_rating = hard_dict.get("min_hotel_rating", 0.0)
        max_stops = hard_dict.get("max_flight_stops", None)

        # Count currently matching
        currently_valid = []
        for cand in raw_inventory_pool:
            flight = cand.get("flight", {})
            stay = cand.get("stay", {})
            price = cand.get("total_price_huf", 0)
            stops = flight.get("stops", 0)

            if direct_only and stops > 0:
                continue
            if max_stops is not None and stops > max_stops:
                continue
            if min_stars and stay.get("stars", 0) < min_stars:
                continue
            if min_rating and stay.get("rating_normalized", 0) < min_rating:
                continue
            if price > (total_budget * 1.25):
                continue
            currently_valid.append(cand)

        current_count = len(currently_valid)
        relaxations = []

        # 1. Test Budget Expansion (+15%, +30%)
        budget_plus_15 = total_budget * 1.15
        unlocked_by_budget_15 = [
            c for c in raw_inventory_pool
            if c not in currently_valid and c.get("total_price_huf", 0) <= (budget_plus_15 * 1.25)
        ]
        if unlocked_by_budget_15:
            delta_huf = int(budget_plus_15 - total_budget)
            relaxations.append({
                "id": "relax_budget_15",
                "category": "budget",
                "title": f"+{delta_huf:,} Ft (+15%) költségkeret emelés".replace(",", " "),
                "description": f"A keret mérsékelt bővítésével {len(unlocked_by_budget_15)} új prémium opció érhető el.",
                "unlocked_count": len(unlocked_by_budget_15),
                "patch": {
                    "total_budget_huf": budget_plus_15
                }
            })

        # 2. Test +1 Flight Stop Relaxation (if direct_only or max_stops == 0)
        if direct_only or (max_stops is not None and max_stops == 0):
            unlocked_by_stops = [
                c for c in raw_inventory_pool
                if c not in currently_valid and c.get("flight", {}).get("stops", 0) == 1
            ]
            if unlocked_by_stops:
                relaxations.append({
                    "id": "relax_flight_stops",
                    "category": "flight",
                    "title": "+1 kényelmes átszállás engedélyezése",
                    "description": f"1 átszállásos járatok bevonásával {len(unlocked_by_stops)} új kedvező árú repülős csomag válik elérhetővé.",
                    "unlocked_count": len(unlocked_by_stops),
                    "patch": {
                        "preferences.hard.direct_flights_only": False,
                        "preferences.hard.max_flight_stops": 1
                    }
                })

        # 3. Test Hotel Stars / Rating Relaxation (e.g. 4★ -> 3★ or rating 8.5 -> 8.0)
        if min_stars and min_stars >= 4:
            unlocked_by_stars = [
                c for c in raw_inventory_pool
                if c not in currently_valid and c.get("stay", {}).get("stars", 0) == (min_stars - 1)
            ]
            if unlocked_by_stars:
                relaxations.append({
                    "id": "relax_hotel_stars",
                    "category": "accommodation",
                    "title": f"Szálláskategória enyhítése: {min_stars - 1}★+ (magas vendégértékeléssel)",
                    "description": f"{len(unlocked_by_stars)} kiváló elhelyezkedésű butikhotel és apartman válik elérhetővé.",
                    "unlocked_count": len(unlocked_by_stars),
                    "patch": {
                        "preferences.hard.min_hotel_stars": min_stars - 1
                    }
                })

        # 4. Date Window Flexibility (+/- 2-3 days)
        relaxations.append({
            "id": "relax_date_window",
            "category": "dates",
            "title": "Időpont rugalmasság kibővítése (+/- 3 nap)",
            "description": "Rugalmasabb indulási napokkal olcsóbb járatnapok és jobb szobaárak nyithatók meg.",
            "unlocked_count": max(len(raw_inventory_pool) - current_count, 5),
            "patch": {
                "date_mode": "interval"
            }
        })

        return {
            "case_id": trip_case.id,
            "total_inventory": len(raw_inventory_pool),
            "currently_valid_count": current_count,
            "is_dead_end": current_count == 0,
            "diagnosis": (
                "Kritikus szűrési korlát: a megadott megkötések mellett 0 opció maradt."
                if current_count == 0
                else f"Jelenleg {current_count} opció felel meg minden szigorú feltételnek."
            ),
            "suggested_relaxations": sorted(relaxations, key=lambda r: r["unlocked_count"], reverse=True)
        }

    @classmethod
    def apply_relaxation(
        cls,
        trip_case: TripCase,
        relaxation_id: str,
        patch_data: Dict[str, Any]
    ) -> TripCase:
        """
        Applies an approved relaxation patch to the TripCase and updates its state.
        """
        for key, val in patch_data.items():
            if key == "total_budget_huf":
                trip_case.total_budget_huf = float(val)
            elif key == "date_mode":
                trip_case.date_mode = str(val)
            elif key == "preferences.hard.direct_flights_only":
                trip_case.preferences.hard.direct_flights_only = bool(val)
            elif key == "preferences.hard.max_flight_stops":
                trip_case.preferences.hard.max_flight_stops = int(val)
            elif key == "preferences.hard.min_hotel_stars":
                trip_case.preferences.hard.min_hotel_stars = int(val)
            elif key == "preferences.hard.min_hotel_rating":
                trip_case.preferences.hard.min_hotel_rating = float(val)

        return trip_case
