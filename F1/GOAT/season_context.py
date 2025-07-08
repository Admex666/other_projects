# season_context.py

import pandas as pd

def compute_season_context(results_df: pd.DataFrame, races_df: pd.DataFrame) -> pd.DataFrame:
    """
    Kiszámolja szezononként a mezőnyre jellemző kontextusadatokat:
    - összes futam
    - versenyzők száma
    - összpontszám
    - átlagos pontverseny/fő
    - szezon győztese pont alapján (modern pontszám alapján)

    Paraméterek:
        results_df (pd.DataFrame): A normalizált pontokat tartalmazó results DataFrame
        races_df (pd.DataFrame): A races.csv DataFrame, amely tartalmazza a season mezőt

    Visszatérés:
        pd.DataFrame: Szezononkénti mezőny-összesítő
    """

    # Csatoljuk a szezonokat a results_df-hez
    results = results_df.merge(races_df[['raceId', 'year']], on='raceId', how='left')

    # Összesített szezonkontextus
    season_group = results.groupby('year')

    context_df = season_group.agg(
        total_races=('raceId', 'nunique'),
        total_drivers=('driverId', pd.Series.nunique),
        total_points=('normalized_points', 'sum'),
        avg_points_per_driver=('normalized_points', lambda x: x.sum() / x.nunique()),
        avg_points_per_race=('normalized_points', 'mean'),
    ).reset_index()

    # Maximum pontszerző versenyző szezononként (dominancia méréshez hasznos)
    max_points_per_driver = (
        results.groupby(['year', 'driverId'])['normalized_points']
        .sum()
        .reset_index()
    )

    max_driver_points = max_points_per_driver.groupby('year')['normalized_points'].max().reset_index()
    max_driver_points.rename(columns={'normalized_points': 'max_driver_points'}, inplace=True)

    context_df = context_df.merge(max_driver_points, on='year', how='left')

    return context_df
