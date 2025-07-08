# metrics.py

import pandas as pd

def calculate_driver_metrics(results_df: pd.DataFrame, qualifying_df: pd.DataFrame) -> pd.DataFrame:
    """
    Visszaad egy DataFrame-t, amely versenyzőnként tartalmazza az alap metrikákat:
    - győzelmek
    - versenyek száma
    - pole pozíciók
    - átlagos versenyhelyezés
    - átlagos kvalifikációs helyezés

    Paraméterek:
        results_df (pd.DataFrame): results.csv adatok normalizált pontokkal
        qualifying_df (pd.DataFrame): qualifying.csv adatok

    Visszatérés:
        pd.DataFrame: versenyzőnkénti metrikák
    """

    # -- Győzelmek és átlagos versenyhelyezés --
    result_stats = results_df.copy()
    result_stats = result_stats[result_stats['position'].notna()]
    result_stats['position'] = pd.to_numeric(result_stats['position'], errors='coerce')

    race_metrics = result_stats.groupby('driverId').agg(
        races=('raceId', 'count'),
        wins=('position', lambda x: (x == 1).sum()),
        avg_finish=('position', 'mean'),
        total_points=('normalized_points', 'sum'),
        avg_points=('normalized_points', 'mean')
    )

    # -- Pole pozíciók és kvalifikációs átlag --
    qual_stats = qualifying_df.copy()
    qual_stats = qual_stats[qual_stats['position'].notna()]
    qual_stats['position'] = pd.to_numeric(qual_stats['position'], errors='coerce')

    qual_metrics = qual_stats.groupby('driverId').agg(
        poles=('position', lambda x: (x == 1).sum()),
        avg_qualifying=('position', 'mean')
    )

    # -- Összekapcsolás --
    driver_metrics = race_metrics.merge(qual_metrics, how='left', on='driverId')
    driver_metrics.fillna(0, inplace=True)

    return driver_metrics.reset_index()
