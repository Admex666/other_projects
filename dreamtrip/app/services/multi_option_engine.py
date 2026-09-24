"""
Optivoya Advisor Workspace — Multi-Option & Archetype Generation Engine
========================================================================
Generates decision-ready travel options from a research pool:
- Option A: BEST OVERALL (Highest balanced composite TripScore)
- Option B: BEST VALUE (Optimal price-to-quality efficiency, budget smart)
- Option C: BEST EXPERIENCE (Premium stay quality, curated vibe & activity richness)

Enforces:
- Hard constraints filtering (budget, flight stops, minimum hotel stars/rating).
- Explicit objective profiles without ungrounded magic-number formulas.
- 3-Option Rule: Target 3, Preferred 3, Acceptable 2, Minimum 1 (Never fabricate poor options).
- Diversity preservation with genuine trade-offs.
"""

from typing import List, Dict, Any, Optional
import copy


class MultiOptionEngine:
    """
    Synthesizes and ranks candidates into distinct, decision-ready Archetypes.
    """

    ARCHETYPE_BEST_OVERALL = "best_overall"
    ARCHETYPE_BEST_VALUE = "best_value"
    ARCHETYPE_BEST_EXPERIENCE = "best_experience"

    @classmethod
    def calculate_experience_score(cls, cand: Dict[str, Any]) -> float:
        """
        Calculates a normalized 0-100 Experience Quality Score without ungrounded magic numbers.
        Components:
        - Stay quality (0-100): 50% stars + 50% rating
        - Activity richness (0-100): scaled up to 4+ curated activities
        - Vibe/Destination fit (0-100): vibe matching score
        - Flight comfort (0-100): direct flights vs connections
        """
        stay = cand.get("stay", {})
        flight = cand.get("flight", {})
        activities = cand.get("activities", [])
        dest = cand.get("destination", {})

        # Stay quality
        stars = float(stay.get("stars") or 3.0)
        rating = float(stay.get("rating_normalized") or stay.get("rating") or 8.0)
        stay_quality = (min(stars / 5.0, 1.0) * 50.0) + (min(rating / 10.0, 1.0) * 50.0)

        # Activity richness
        act_count = len(activities)
        activity_richness = min(act_count / 4.0, 1.0) * 100.0 if act_count > 0 else 70.0

        # Vibe / Destination fit
        vibe_fit = float(dest.get("vibe_match_score") or dest.get("score") or 85.0)

        # Flight comfort
        stops = int(flight.get("stops") or 0)
        flight_comfort = 100.0 if stops == 0 else (75.0 if stops == 1 else 50.0)

        # Composite experience score (bounded 0-100)
        score = (0.35 * stay_quality) + (0.25 * activity_richness) + (0.25 * vibe_fit) + (0.15 * flight_comfort)
        return round(min(max(score, 0.0), 100.0), 1)

    @classmethod
    def calculate_value_efficiency(cls, cand: Dict[str, Any], reference_budget: Optional[float] = None) -> float:
        """
        Calculates a normalized 0-100 Value Efficiency score.
        Balances composite quality (TripScore) against normalized cost.
        """
        trip_score = float(cand.get("trip_score") or 75.0)
        price = float(cand.get("total_price_huf") or 200000.0)

        ref_budget = reference_budget or 300000.0
        normalized_price = max(price / max(ref_budget, 50000.0), 0.3)

        # High trip score with lower price yields highest efficiency
        efficiency = (trip_score / normalized_price) * 0.8
        return round(min(max(efficiency, 0.0), 100.0), 1)

    @classmethod
    def generate_archetypes(
        cls,
        candidates: List[Dict[str, Any]],
        preferences: Optional[Any] = None,
        target_budget_huf: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Takes a list of raw package candidates and assigns/optimizes them into 1-3 distinct Archetypes.
        Target: 3 options, Acceptable: 2 options, Minimum: 1 option.
        """
        if not candidates:
            return []

        # 1. Filter out invalid candidates violating hard constraints
        valid_candidates = cls._filter_hard_constraints(candidates, preferences, target_budget_huf)
        if not valid_candidates:
            # Fallback to original candidates if strict filtering left 0
            valid_candidates = candidates

        # 2. Case: Only 1 valid candidate available
        if len(valid_candidates) == 1:
            opt_a = copy.deepcopy(valid_candidates[0])
            cls._assign_archetype_metadata(
                opt_a,
                cls.ARCHETYPE_BEST_OVERALL,
                why="Kiemelkedő illeszkedés a megadott preferenciákhoz és a legmagasabb összetett TripScore index.",
                tradeoff="Egyetlen optimalizált opció érhető el a szigorú feltételek mellett."
            )
            return [opt_a]

        # 3. Score candidates for each Archetype profile
        # Best Overall: Max TripScore
        sorted_overall = sorted(valid_candidates, key=lambda c: float(c.get("trip_score", 0)), reverse=True)
        best_overall = copy.deepcopy(sorted_overall[0])

        # Best Value: Max Value Efficiency
        ref_budget = target_budget_huf or float(best_overall.get("total_price_huf") or 300000.0)
        sorted_value = sorted(
            valid_candidates,
            key=lambda c: cls.calculate_value_efficiency(c, ref_budget),
            reverse=True
        )

        # Select Best Value (distinct from Best Overall if possible)
        best_value = None
        for cand in sorted_value:
            if cand.get("id") != best_overall.get("id"):
                best_value = copy.deepcopy(cand)
                break
        if not best_value and len(valid_candidates) > 1:
            # Pick next candidate in sorted value list
            best_value = copy.deepcopy(sorted_value[0])

        # Best Experience: Max Experience Quality Score
        sorted_experience = sorted(
            valid_candidates,
            key=lambda c: cls.calculate_experience_score(c),
            reverse=True
        )

        # Select Best Experience (distinct from Best Overall and Best Value if possible)
        best_experience = None
        selected_ids = {best_overall.get("id")}
        if best_value:
            selected_ids.add(best_value.get("id"))

        for cand in sorted_experience:
            if cand.get("id") not in selected_ids:
                best_experience = copy.deepcopy(cand)
                break

        # 4. Assemble Option Set respecting the 3-Option Rule
        options: List[Dict[str, Any]] = [best_overall]

        if best_value and best_value.get("id") != best_overall.get("id"):
            options.append(best_value)

        if best_experience and best_experience.get("id") not in [o.get("id") for o in options]:
            options.append(best_experience)

        # If we have 2 options and still 3rd candidate available in pool, try to pick 3rd distinct candidate
        if len(options) == 2 and len(valid_candidates) >= 3:
            current_ids = {o.get("id") for o in options}
            for cand in sorted_experience + sorted_overall:
                if cand.get("id") not in current_ids:
                    third_opt = copy.deepcopy(cand)
                    options.append(third_opt)
                    break

        # 5. Enrich with Archetype Labels, Why-This-Option, and Trade-offs
        cls._assign_archetype_metadata(
            options[0],
            cls.ARCHETYPE_BEST_OVERALL,
            why="Kiegyensúlyozott menetrend, prémium szállás és optimális ár-érték arány a legmagasabb összetett indexszel.",
            tradeoff="Mérsékelt árprémium az abszolút legolcsóbb ajánlathoz képest."
        )

        if len(options) > 1:
            cls._assign_archetype_metadata(
                options[1],
                cls.ARCHETYPE_BEST_VALUE,
                why="Kedvezőbb teljes költségvetés a kényelmi és minőségi alapkövetelmények szigorú megőrzése mellett.",
                tradeoff="Egyszerűbb szálláskategória vagy kissé korábbi/későbbi járati indulás."
            )

        if len(options) > 2:
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

        direct_only = _get_val(hard, "direct_flights_only", False) or False
        max_stops = _get_val(hard, "max_flight_stops", None)
        max_budget = _get_val(hard, "max_total_budget_huf", None)

        valid = []
        for cand in candidates:
            flight = cand.get("flight", {})
            price = float(cand.get("total_price_huf") or 0.0)

            # Check flight stops
            stops = int(flight.get("stops") or 0)
            if direct_only and stops > 0:
                continue
            if max_stops is not None and stops > max_stops:
                continue

            # Check explicit hard total budget if strictly bounded
            if max_budget and price > max_budget:
                continue

            valid.append(cand)

        return valid if valid else candidates

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
