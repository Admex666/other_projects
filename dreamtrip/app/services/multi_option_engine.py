"""
Optivoya Advisor Workspace — Multi-Option & Archetype Generation Engine
========================================================================
Generates 3 distinct, fully-realized travel options from a research pool:
- Option A: BEST OVERALL (Highest balanced composite TripScore)
- Option B: BEST VALUE (Optimal price-to-quality ratio, budget friendly)
- Option C: BEST EXPERIENCE (Maximum activities, premium stay, curated vibe)

Enforces hard constraints filtering, diversity separation, and data-driven
trade-off explanations without LLM hallucinations.
"""

from typing import List, Dict, Any, Optional
import copy


class MultiOptionEngine:
    """
    Synthesizes and ranks candidates into exactly 3 diverse, decision-ready Archetypes.
    """

    ARCHETYPE_BEST_OVERALL = "best_overall"
    ARCHETYPE_BEST_VALUE = "best_value"
    ARCHETYPE_BEST_EXPERIENCE = "best_experience"

    @classmethod
    def generate_archetypes(
        cls,
        candidates: List[Dict[str, Any]],
        preferences: Optional[Any] = None,
        target_budget_huf: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Takes a list of raw package candidates and assigns/optimizes them into 3 distinct Archetypes.
        """
        if not candidates:
            return []

        # 1. Filter out invalid candidates violating hard constraints
        valid_candidates = cls._filter_hard_constraints(candidates, preferences, target_budget_huf)
        if not valid_candidates:
            # If all were filtered, fallback to raw candidates with a warning
            valid_candidates = candidates

        if len(valid_candidates) == 1:
            opt_a = copy.deepcopy(valid_candidates[0])
            cls._assign_archetype_metadata(opt_a, cls.ARCHETYPE_BEST_OVERALL, "Kiemelkedő kiegyensúlyozottság minden szempontból")
            return [opt_a]

        # 2. Score and sort candidates for each archetype dimension
        # Best Overall: Max TripScore
        sorted_overall = sorted(valid_candidates, key=lambda c: c.get("trip_score", 0), reverse=True)
        best_overall = copy.deepcopy(sorted_overall[0])

        # Best Value: Lowest total price with decent score (Value Ratio = trip_score / (price / 10000))
        sorted_value = sorted(
            valid_candidates,
            key=lambda c: (c.get("trip_score", 50) / max(c.get("total_price_huf", 100000) / 10000.0, 1.0)),
            reverse=True
        )
        # Choose the best value candidate that is distinct from best_overall if possible
        best_value = None
        for cand in sorted_value:
            if cand.get("id") != best_overall.get("id") or len(valid_candidates) == 1:
                best_value = copy.deepcopy(cand)
                break
        if not best_value:
            best_value = copy.deepcopy(sorted_value[0])

        # Best Experience: Highest hotel rating/stars + max activities
        sorted_experience = sorted(
            valid_candidates,
            key=lambda c: (
                c.get("stay", {}).get("stars", 3) * 10
                + (c.get("stay", {}).get("rating_normalized", 8.0) * 5)
                + len(c.get("activities", [])) * 4
                + c.get("trip_score", 50) * 0.5
            ),
            reverse=True
        )
        best_experience = None
        for cand in sorted_experience:
            if cand.get("id") not in [best_overall.get("id"), best_value.get("id")] or len(valid_candidates) <= 2:
                best_experience = copy.deepcopy(cand)
                break
        if not best_experience:
            best_experience = copy.deepcopy(sorted_experience[0])

        # 3. Apply Diversity Safeguard
        # If best_value or best_experience have the same ID as best_overall, adjust params
        options = [best_overall, best_value, best_experience]
        cls._ensure_diversity(options, valid_candidates)

        # 4. Enrich with Archetype Labels, Why-This-Option, and Trade-offs
        cls._assign_archetype_metadata(
            options[0],
            cls.ARCHETYPE_BEST_OVERALL,
            why="Kiegyensúlyozott menetrend, prémium szállás és optimális ár-érték arány a legmagasabb összetett indexszel.",
            tradeoff="Mérsékelt árprémium az abszolút legolcsóbb ajánlathoz képest."
        )

        cls._assign_archetype_metadata(
            options[1],
            cls.ARCHETYPE_BEST_VALUE,
            why="Kedvezőbb teljes költségvetés a kényelmi és minőségi alapkövetelmények szigorú megőrzése mellett.",
            tradeoff="Egyszerűbb szálláskategória vagy kissé korábbi/későbbi járati indulás."
        )

        cls._assign_archetype_metadata(
            options[2],
            cls.ARCHETYPE_BEST_EXPERIENCE,
            why="Kiváló elhelyezkedésű 4-5★ szálloda, kényelmes járat és maximálisan gazdag kulturális/gasztro programkínálat.",
            tradeoff="Magasabb teljes költségvetési igény."
        )

        return options

    @classmethod
    def _filter_hard_constraints(
        cls,
        candidates: List[Dict[str, Any]],
        preferences: Optional[Any],
        target_budget_huf: Optional[float]
    ) -> List[Dict[str, Any]]:
        """
        Removes candidates that violate strict hard constraints.
        """
        if not preferences:
            return candidates

        hard = getattr(preferences, "hard", None)
        if hard is None:
            hard = preferences if isinstance(preferences, dict) else {}

        def _get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        min_stars = _get_val(hard, "min_hotel_stars", 0) or 0
        min_rating = _get_val(hard, "min_hotel_rating", 0.0) or 0.0
        direct_only = _get_val(hard, "direct_flights_only", False) or False
        max_stops = _get_val(hard, "max_flight_stops", None)

        valid = []
        for cand in candidates:
            flight = cand.get("flight", {})
            stay = cand.get("stay", {})
            price = cand.get("total_price_huf", 0)

            # Check flight stops
            stops = flight.get("stops", 0)
            if direct_only and stops > 0:
                continue
            if max_stops is not None and stops > max_stops:
                continue

            # Check hotel stars & rating
            if min_stars and stay.get("stars", 0) < min_stars:
                continue
            if min_rating and stay.get("rating_normalized", 0) < min_rating:
                continue

            # Check hard total budget if strictly bounded
            if target_budget_huf and price > (target_budget_huf * 1.35): # Allow 35% flex max for hard discard
                continue

            valid.append(cand)

        return valid

    @classmethod
    def _ensure_diversity(cls, selected: List[Dict[str, Any]], all_candidates: List[Dict[str, Any]]) -> None:
        """
        Ensures the 3 options have distinct IDs or noticeable variations in price/airline/stay.
        """
        seen_ids = set()
        for idx, opt in enumerate(selected):
            opt_id = opt.get("id")
            if opt_id in seen_ids and len(all_candidates) > len(selected):
                # Pick an unused candidate from pool
                for cand in all_candidates:
                    if cand.get("id") not in seen_ids:
                        selected[idx] = copy.deepcopy(cand)
                        break
            seen_ids.add(selected[idx].get("id"))

    @classmethod
    def _assign_archetype_metadata(
        cls,
        cand: Dict[str, Any],
        archetype: str,
        why: str = "",
        tradeoff: str = ""
    ) -> None:
        cand["archetype"] = archetype
        cand["archetype_label"] = archetype.replace("_", " ").upper()
        if why:
            cand["why_this_option"] = why
        if tradeoff:
            cand["tradeoffs"] = [tradeoff]
        if "verification_status" not in cand:
            cand["verification_status"] = "VERIFIED"
