"""
Optivoya Advisor Workspace v2 — Dynamic Requirement Discovery & Preference Engine
==================================================================================
Implements:
1. Two-Stage Preference Discovery:
   - Stage 1: Relevant Dimension Selection (from 9 canonical travel dimensions).
   - Stage 2: Pairwise AHP Weighting exclusively on the selected active dimensions.
2. 4-Level Structured Criteria Management:
   - HARD (Pass/Fail constraints)
   - SOFT (Normalized AHP weights on active dimensions)
   - AVOID (Negative filters)
   - NICE_TO_HAVE (Score bonuses)
3. Mathematical AHP solver with Consistency Ratio (CR) calculation & auto-harmonization.
4. Real-time synchronization with ResolvedTripPreferences & ResearchState.what_matters.
"""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.models.advisor_models import (
    TripCase, ResolvedTripPreferences, HardConstraints, SoftPreferences,
    AvoidRules, NiceToHave, ResearchState
)
from app.services.research_state_service import ResearchStateService

logger = logging.getLogger("preference_discovery_service")

# Random Consistency Index (RI) table for matrix sizes 1..10
_AHP_RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49
}

# Canonical 9 Travel Decision Dimensions Catalog
CANONICAL_DIMENSIONS = [
    {
        "id": "price",
        "name": "Költségvetés & Ár-érték",
        "description": "A teljes utazási költség és az ár-érték arány maximalizálása",
        "icon": "payments",
        "default_active": True,
        "category": "core"
    },
    {
        "id": "flight_comfort",
        "name": "Repülés Kényelme",
        "description": "Közvetlen járatok, optimális indulási idősávok és alacsony utazási idő",
        "icon": "flight_takeoff",
        "default_active": True,
        "category": "logistics"
    },
    {
        "id": "location",
        "name": "Központi Lokáció",
        "description": "Belvárosi elhelyezkedés, jó tömegközlekedés és rövid sétaidők",
        "icon": "location_on",
        "default_active": True,
        "category": "stay"
    },
    {
        "id": "hotel_quality",
        "name": "Szállás Minőség & Csillagok",
        "description": "Magas vendégértékelés (8.8+), 4-5★ kategória és prémium szobák",
        "icon": "hotel",
        "default_active": True,
        "category": "stay"
    },
    {
        "id": "beach",
        "name": "Tengerpart & Strand",
        "description": "Közvetlen tengerparti vagy vízparti elhelyezkedés, jó strandminőség",
        "icon": "beach_access",
        "default_active": False,
        "category": "leisure"
    },
    {
        "id": "gastronomy",
        "name": "Gasztronómia & Étlap",
        "description": "Kiemelkedő helyi éttermek, Michelin-ajánlások és kulináris élmények",
        "icon": "restaurant",
        "default_active": False,
        "category": "experience"
    },
    {
        "id": "culture_sightseeing",
        "name": "Kultúra & Látnivalók",
        "description": "Történelmi műemlékek, világhírű múzeumok és gazdag városnézés",
        "icon": "museum",
        "default_active": True,
        "category": "experience"
    },
    {
        "id": "relaxation_wellness",
        "name": "Nyugalom & Wellness",
        "description": "Csendes környezet, spa & wellness lehetőségek, pihenés",
        "icon": "spa",
        "default_active": False,
        "category": "leisure"
    },
    {
        "id": "family_friendliness",
        "name": "Családbarát Megoldások",
        "description": "Gyermekprogramok, családi szobák és biztonságos környezet",
        "icon": "family_restroom",
        "default_active": False,
        "category": "core"
    }
]


class PreferenceDiscoveryService:
    """
    Service managing 2-stage dynamic requirement discovery and AHP calculations.
    """

    @classmethod
    def get_dimension_catalog(cls) -> List[Dict[str, Any]]:
        """Returns the full catalog of available travel dimensions."""
        return CANONICAL_DIMENSIONS

    @classmethod
    def generate_minimal_ahp_pairs(cls, selected_dimensions: List[str]) -> List[Dict[str, Any]]:
        """
        Generates the minimal set of pairwise comparisons for the active selected dimensions.
        For n selected dimensions, creates n*(n-1)/2 pairs with intuitive labels.
        """
        if not selected_dimensions or len(selected_dimensions) < 2:
            return []

        dim_map = {d["id"]: d for d in CANONICAL_DIMENSIONS}
        valid_dims = [d for d in selected_dimensions if d in dim_map]
        n = len(valid_dims)

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                dim_a = dim_map[valid_dims[i]]
                dim_b = dim_map[valid_dims[j]]
                pairs.append({
                    "pair_id": f"{dim_a['id']}__vs__{dim_b['id']}",
                    "dim_a": dim_a["id"],
                    "dim_a_label": dim_a["name"],
                    "dim_a_icon": dim_a["icon"],
                    "dim_b": dim_b["id"],
                    "dim_b_label": dim_b["name"],
                    "dim_b_icon": dim_b["icon"],
                    "current_ratio": 1.0,  # 1.0 = Equal importance, >1 favors A, <1 favors B
                    "description": f"Hasonlítsd össze: {dim_a['name']} vs. {dim_b['name']}"
                })

        return pairs

    @classmethod
    def calculate_ahp_weights(
        cls,
        selected_dimensions: List[str],
        comparisons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates normalized AHP weights (sum = 1.0) and evaluates the Consistency Ratio (CR).
        Uses the geometric mean method (Logarithmic Least Squares) for principal eigenvector estimation.
        """
        dim_map = {d["id"]: d for d in CANONICAL_DIMENSIONS}
        valid_dims = [d for d in selected_dimensions if d in dim_map]
        n = len(valid_dims)

        if n == 0:
            return {"weights": {}, "consistency_ratio": 0.0, "is_consistent": True}
        if n == 1:
            return {"weights": {valid_dims[0]: 1.0}, "consistency_ratio": 0.0, "is_consistent": True}

        # Build n x n comparison matrix
        dim_index = {dim: idx for idx, dim in enumerate(valid_dims)}
        matrix = [[1.0 for _ in range(n)] for _ in range(n)]

        # Populate from comparisons
        for comp in comparisons:
            a = comp.get("dim_a")
            b = comp.get("dim_b")
            ratio = float(comp.get("ratio", comp.get("current_ratio", 1.0)))

            if a in dim_index and b in dim_index:
                idx_a = dim_index[a]
                idx_b = dim_index[b]
                # Ratio must be positive
                ratio = max(0.111, min(9.0, ratio))
                matrix[idx_a][idx_b] = ratio
                matrix[idx_b][idx_a] = 1.0 / ratio

        # 1. Geometric mean for each row
        geom_means = []
        for i in range(n):
            prod = 1.0
            for j in range(n):
                prod *= matrix[i][j]
            geom_means.append(math.pow(prod, 1.0 / n))

        sum_geom = sum(geom_means)
        if sum_geom <= 0:
            sum_geom = 1.0

        # 2. Normalized weights
        weights = {valid_dims[i]: round(geom_means[i] / sum_geom, 4) for i in range(n)}

        # 3. Calculate lambda_max and Consistency Ratio
        # A * w vector
        aw = [0.0] * n
        for i in range(n):
            for j in range(n):
                aw[i] += matrix[i][j] * (geom_means[j] / sum_geom)

        lambda_max = sum(aw[i] / (geom_means[i] / sum_geom) for i in range(n)) / n

        # CI & CR
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = _AHP_RI_TABLE.get(n, 1.45)
        cr = (ci / ri) if ri > 0 else 0.0

        is_consistent = (cr <= 0.12)  # 10-12% tolerance

        return {
            "weights": weights,
            "lambda_max": round(lambda_max, 4),
            "consistency_index": round(ci, 4),
            "consistency_ratio": round(cr, 4),
            "is_consistent": is_consistent,
            "dimensions_count": n
        }

    @classmethod
    def get_case_criteria(cls, trip_case: TripCase) -> Dict[str, Any]:
        """
        Returns the current resolved 4-level criteria and active dimensions for a Case.
        """
        prefs = trip_case.preferences or ResolvedTripPreferences()
        research_state = ResearchStateService.get_or_create_research_state(trip_case=trip_case)
        matters = research_state.what_matters

        selected_dims = matters.selected_dimensions or ["price", "flight_comfort", "location", "hotel_quality"]
        pairs = cls.generate_minimal_ahp_pairs(selected_dims)

        return {
            "case_id": trip_case.id,
            "selected_dimensions": selected_dims,
            "dimension_catalog": CANONICAL_DIMENSIONS,
            "ahp_weights": matters.ahp_weights or prefs.soft.vibe_weights,
            "ahp_pairs": pairs,
            "hard_constraints": prefs.hard.model_dump(),
            "soft_preferences": prefs.soft.model_dump(),
            "avoid_rules": prefs.avoid.model_dump(),
            "nice_to_have": prefs.nice_to_have.model_dump()
        }

    @classmethod
    def update_case_criteria(
        cls,
        trip_case: TripCase,
        selected_dimensions: Optional[List[str]] = None,
        ahp_weights: Optional[Dict[str, float]] = None,
        hard_updates: Optional[Dict[str, Any]] = None,
        avoid_updates: Optional[Dict[str, Any]] = None,
        nice_to_have_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Updates the 4-level criteria structure and synchronizes both TripCase and ResearchState.
        """
        prefs = trip_case.preferences or ResolvedTripPreferences()
        research_state = ResearchStateService.get_or_create_research_state(trip_case=trip_case)
        matters = research_state.what_matters

        # 1. Update selected dimensions if provided
        if selected_dimensions is not None:
            valid_set = {d["id"] for d in CANONICAL_DIMENSIONS}
            filtered_dims = [d for d in selected_dimensions if d in valid_set]
            matters.selected_dimensions = filtered_dims

            # If no weights provided, distribute equally or recalculate
            if not ahp_weights:
                equal_w = round(1.0 / len(filtered_dims), 4) if filtered_dims else 0.0
                matters.ahp_weights = {d: equal_w for d in filtered_dims}

        # 2. Update AHP weights if provided
        if ahp_weights:
            matters.ahp_weights = ahp_weights
            # Mirror to soft preferences
            prefs.soft.vibe_weights.update(ahp_weights)

        # 3. Update Hard constraints
        if hard_updates:
            for k, v in hard_updates.items():
                if hasattr(prefs.hard, k):
                    setattr(prefs.hard, k, v)
            matters.hard_constraints.update(hard_updates)

        # 4. Update Avoid rules
        if avoid_updates:
            for k, v in avoid_updates.items():
                if hasattr(prefs.avoid, k):
                    setattr(prefs.avoid, k, v)

        # 5. Update Nice-to-have rules
        if nice_to_have_updates:
            for k, v in nice_to_have_updates.items():
                if hasattr(prefs.nice_to_have, k):
                    setattr(prefs.nice_to_have, k, v)

        trip_case.preferences = prefs
        research_state.what_still_needs_decision.criteria_approved = True

        return cls.get_case_criteria(trip_case)
