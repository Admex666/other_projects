# normalize_points.py

import pandas as pd

# Modern F1 pontrendszer: helyezés -> pont
MODERN_POINTS = {
    1: 25,
    2: 18,
    3: 15,
    4: 12,
    5: 10,
    6: 8,
    7: 6,
    8: 4,
    9: 2,
    10: 1
    # 11+ helyezettek: 0 pont
}

def apply_normalized_points(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Hozzáad egy 'normalized_points' oszlopot a results_df-hez,
    amely a modern pontrendszer alapján számol.
    
    Paraméterek:
        results_df (pd.DataFrame): A 'results.csv'-ből beolvasott DataFrame.
    
    Visszatérés:
        pd.DataFrame: Új oszloppal bővített DataFrame.
    """

    def get_points(position):
        try:
            pos = int(position)
            return MODERN_POINTS.get(pos, 0)
        except:
            return 0  # DNF, DSQ, NaN, stb.

    results_df = results_df.copy()
    results_df['normalized_points'] = results_df['position'].apply(get_points)
    return results_df
