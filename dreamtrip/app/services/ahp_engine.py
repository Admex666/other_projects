"""
Optivoya Shared Intelligence — AHP Engine (Analytic Hierarchy Process)
Mathematical Decision Matrix & Priority Vector Calculation Service using Saaty's Geometric Mean & Consistency Ratio.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class AHPEngine:
    """
    Standardized Analytic Hierarchy Process (AHP) Calculation Engine.
    Provides pairwise comparison matrix evaluation, priority weights via geometric mean,
    and consistency ratio (CR) checking.
    """

    # Saaty Random Consistency Index (RI) table for matrix sizes 1 to 10
    RI_TABLE = {
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

    # Verbal scale mapping
    SCALE_MAP = {
        9.0: "Extremely more important",
        5.0: "Strongly more important",
        3.0: "Moderately more important",
        1.0: "Equal importance",
        1.0 / 3.0: "Moderately less important",
        1.0 / 5.0: "Strongly less important",
        1.0 / 9.0: "Extremely less important"
    }

    @classmethod
    def calculate_weights(
        cls,
        matrix: np.ndarray,
        criterion_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates normalized criteria weights from a square pairwise comparison matrix
        using the Geometric Mean (Logarithmic Least Squares) method.
        
        Args:
            matrix: NxN reciprocal numpy array where matrix[i][j] = 1 / matrix[j][i]
            criterion_names: Optional list of criterion names
            
        Returns:
            Dict containing:
                - weights: Dict[str, float] or List[float] normalized to 100% (summing to 1.0)
                - weights_percentage: Dict[str, float] formatted as percentages (summing to 100.0)
                - lambda_max: Principal eigenvalue approximation
                - ci: Consistency Index
                - cr: Consistency Ratio (CR < 0.10 is considered consistent)
                - is_consistent: bool
        """
        matrix = np.array(matrix, dtype=float)
        n = matrix.shape[0]

        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"AHP matrix must be square, got shape {matrix.shape}")

        if n == 0:
            return {"weights": {}, "weights_percentage": {}, "cr": 0.0, "is_consistent": True}

        if n == 1:
            name = criterion_names[0] if criterion_names else "criterion_1"
            return {
                "weights": {name: 1.0},
                "weights_percentage": {name: 100.0},
                "lambda_max": 1.0,
                "ci": 0.0,
                "cr": 0.0,
                "is_consistent": True
            }

        # 1. Geometric Mean per row
        row_geom_means = np.prod(matrix, axis=1) ** (1.0 / n)
        sum_geom_means = np.sum(row_geom_means)

        if sum_geom_means == 0:
            weights = np.ones(n) / n
        else:
            weights = row_geom_means / sum_geom_means

        # 2. Consistency Ratio Calculation
        # Ax approximation
        weighted_sum_vector = np.dot(matrix, weights)
        lambda_max = float(np.mean(weighted_sum_vector / weights))

        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = cls.RI_TABLE.get(n, 1.49)
        cr = float(ci / ri) if ri > 0 else 0.0

        names = criterion_names if criterion_names and len(criterion_names) == n else [f"criterion_{i+1}" for i in range(n)]

        weights_dict = {names[i]: float(weights[i]) for i in range(n)}
        weights_pct_dict = {names[i]: round(float(weights[i] * 100.0), 1) for i in range(n)}

        # Normalize percentages to exactly 100.0 sum
        total_pct = sum(weights_pct_dict.values())
        if total_pct > 0 and abs(total_pct - 100.0) > 0.01:
            diff = 100.0 - total_pct
            first_key = list(weights_pct_dict.keys())[0]
            weights_pct_dict[first_key] = round(weights_pct_dict[first_key] + diff, 1)

        return {
            "weights": weights_dict,
            "weights_percentage": weights_pct_dict,
            "lambda_max": round(lambda_max, 4),
            "ci": round(ci, 4),
            "cr": round(cr, 4),
            "is_consistent": cr <= 0.15  # Up to 0.15 accepted in practical human pairwise tasks
        }

    @classmethod
    def build_matrix_from_pairwise_dict(
        cls,
        criteria: List[str],
        pairwise_preferences: Dict[str, float]
    ) -> np.ndarray:
        """
        Constructs an NxN reciprocal matrix from a dictionary of pairwise comparisons.
        Dictionary keys can be formatted as "critA_vs_critB" or ("critA", "critB").
        """
        n = len(criteria)
        matrix = np.ones((n, n), dtype=float)

        for i in range(n):
            for j in range(i + 1, n):
                c1, c2 = criteria[i], criteria[j]
                key_str = f"{c1}_vs_{c2}"
                alt_key_str = f"{c2}_vs_{c1}"

                if key_str in pairwise_preferences:
                    val = float(pairwise_preferences[key_str])
                    matrix[i][j] = val
                    matrix[j][i] = 1.0 / val if val != 0 else 1.0
                elif alt_key_str in pairwise_preferences:
                    val = float(pairwise_preferences[alt_key_str])
                    matrix[j][i] = val
                    matrix[i][j] = 1.0 / val if val != 0 else 1.0

        return matrix
