"""
Optivoya Shared Intelligence — PROMETHEE II Engine
Multi-Criteria Decision Analysis (MCDA) Outranking Calculation Service.
Supports Generalized Preference Functions (Types 1 to 6), Min/Max directions, and Net Flow Ranking.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class PrometheeEngine:
    """
    Standardized PROMETHEE II (Preference Ranking Organization METHod for Enrichment Evaluations) Engine.
    Computes unicriterion preference degrees, aggregated multicriteria preference indices,
    positive outranking flow (Phi+), negative outranking flow (Phi-), and net outranking flow (Phi_net).
    """

    @staticmethod
    def evaluate_preference_function(
        diff: float,
        fn_type: int = 5,
        q: float = 0.0,
        p: float = 1.0,
        s: float = 1.0
    ) -> float:
        """
        Evaluates the unicriterion preference degree P(d) where d = g_j(a) - g_j(b).
        If diff <= 0, preference is always 0.0.
        """
        if diff <= 0:
            return 0.0

        if fn_type == 1:
            # Type 1: Usual Criterion
            return 1.0 if diff > 0 else 0.0

        elif fn_type == 2:
            # Type 2: U-shape Criterion (Threshold q)
            return 1.0 if diff > q else 0.0

        elif fn_type == 3:
            # Type 3: V-shape Criterion (Threshold p)
            if diff > p:
                return 1.0
            return diff / p if p > 0 else 1.0

        elif fn_type == 4:
            # Type 4: Level Criterion (Thresholds q, p)
            if diff <= q:
                return 0.0
            elif diff > p:
                return 1.0
            else:
                return 0.5

        elif fn_type == 5:
            # Type 5: V-shape with Indifference Area (Thresholds q, p)
            if diff <= q:
                return 0.0
            elif diff > p:
                return 1.0
            else:
                return (diff - q) / (p - q) if (p - q) > 0 else 1.0

        elif fn_type == 6:
            # Type 6: Gaussian Criterion (Parameter s)
            return 1.0 - np.exp(-(diff ** 2) / (2.0 * (s ** 2))) if s > 0 else 1.0

        # Fallback to linear
        return min(1.0, max(0.0, diff / p)) if p > 0 else 1.0

    @classmethod
    def rank_alternatives(
        cls,
        alternatives: List[Dict[str, Any]],
        criteria_configs: Dict[str, Dict[str, Any]],
        criteria_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Ranks a list of candidate alternatives using PROMETHEE II.
        
        Args:
            alternatives: List of alternative dictionaries containing criteria values.
            criteria_configs: Dict per criterion defining:
                - 'type': int (1-6)
                - 'q': float (indifference threshold)
                - 'p': float (preference threshold)
                - 'direction': 'min' or 'max' (default 'max')
            criteria_weights: Normalized or raw weights per criterion name.
            
        Returns:
            Ranked list of alternatives with attached PROMETHEE metrics:
                - phi_plus: Positive leaving flow
                - phi_minus: Negative entering flow
                - phi_net: Net outranking flow in [-1.0, 1.0]
                - relevance_pct: Normalized percentage in [0, 100]
                - rank: 1-based integer rank
        """
        n = len(alternatives)
        if n == 0:
            return []

        if n == 1:
            res = dict(alternatives[0])
            res.update({"phi_plus": 0.0, "phi_minus": 0.0, "phi_net": 0.0, "relevance_pct": 100, "rank": 1})
            return [res]

        # Normalize criteria weights
        active_criteria = [c for c in criteria_configs.keys() if c in criteria_weights]
        total_w = sum(criteria_weights.get(c, 0.0) for c in active_criteria)
        norm_weights = {c: (criteria_weights[c] / total_w) if total_w > 0 else (1.0 / len(active_criteria)) for c in active_criteria}

        # Pairwise aggregated preference matrix pi(a, b)
        pi_matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                agg_pref = 0.0
                for crit in active_criteria:
                    cfg = criteria_configs[crit]
                    fn_type = cfg.get('type', 5)
                    q = float(cfg.get('q', 0.0))
                    p = float(cfg.get('p', 1.0))
                    s = float(cfg.get('s', 1.0))
                    direction = cfg.get('direction', 'max')

                    val_i = float(alternatives[i].get(crit, 0.0) or 0.0)
                    val_j = float(alternatives[j].get(crit, 0.0) or 0.0)

                    # Compute difference based on optimization direction
                    if direction == 'min':
                        # Lower is better -> i is preferred to j if val_j > val_i
                        diff = val_j - val_i
                    else:
                        # Higher is better -> i is preferred to j if val_i > val_j
                        diff = val_i - val_j

                    pref_degree = cls.evaluate_preference_function(diff, fn_type=fn_type, q=q, p=p, s=s)
                    agg_pref += norm_weights[crit] * pref_degree

                pi_matrix[i][j] = agg_pref

        # Compute Outranking Flows
        phi_plus = np.sum(pi_matrix, axis=1) / (n - 1)
        phi_minus = np.sum(pi_matrix, axis=0) / (n - 1)
        phi_net = phi_plus - phi_minus

        # Attach metrics and sort
        enriched_alternatives = []
        for idx in range(n):
            alt_copy = dict(alternatives[idx])
            p_net = float(phi_net[idx])
            relevance = int(round(max(0.0, min(100.0, (p_net + 1.0) / 2.0 * 100.0))))

            alt_copy.update({
                "phi_plus": round(float(phi_plus[idx]), 4),
                "phi_minus": round(float(phi_minus[idx]), 4),
                "phi_net": round(p_net, 4),
                "relevance_pct": relevance
            })
            enriched_alternatives.append(alt_copy)

        # Sort by phi_net descending
        enriched_alternatives.sort(key=lambda x: x["phi_net"], reverse=True)

        for rank_idx, item in enumerate(enriched_alternatives):
            item["rank"] = rank_idx + 1

        return enriched_alternatives
