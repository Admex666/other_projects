# goat_index.py

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def calculate_goat_index(
    driver_metrics: pd.DataFrame,
    teammate_df: pd.DataFrame,
    min_races: int = 20,
    weights: dict = None
) -> pd.DataFrame:
    """
    A különböző metrikák kombinálásával kiszámolja a GOAT-indexet versenyzőnként.

    Paraméterek:
        driver_metrics (pd.DataFrame): alapversenyzői mutatók
        teammate_df (pd.DataFrame): csapattársi összehasonlítás
        min_races (int): csak azokat számoljuk, akik legalább ennyi futamon indultak
        weights (dict): súlyozás az egyes mutatókra

    Visszatérés:
        pd.DataFrame: GOAT-index-szel bővített versenyzői adatok
    """

    if weights is None:
        weights = {
            'points': 0.15,
            'avg_points': 0.20,
            'win_rate': 0.20,
            'pole_rate': 0.10,
            'teammate_score': 0.35,
        }

    df = driver_metrics.copy()
    df = df[df['races'] >= min_races]

    # Arányos mutatók számítása
    df['win_rate'] = df['wins'] / df['races']
    df['pole_rate'] = df['poles'] / df['races']
    df['avg_points'] = df['total_points'] / df['races']

    # Csapattársi adat hozzáfűzése
    df = df.merge(teammate_df[['driverId', 'teammate_score']], on='driverId', how='left')
    df['teammate_score'] = df['teammate_score'].fillna(0.5)

    # Skálázás (min-max minden mutatóra 0-1 közé)
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(df[[
        'total_points', 'avg_points', 'win_rate', 'pole_rate', 'teammate_score'
    ]])

    df_scaled = pd.DataFrame(scaled_features, columns=[
        'points_scaled', 'avg_points_scaled', 'win_scaled', 'pole_scaled', 'teammate_scaled'
    ])
    df_scaled.index = df.index

    # GOAT-index kiszámítása súlyozottan
    df['goat_index'] = (
        df_scaled['points_scaled'] * weights['points'] +
        df_scaled['avg_points_scaled'] * weights['avg_points'] +
        df_scaled['win_scaled'] * weights['win_rate'] +
        df_scaled['pole_scaled'] * weights['pole_rate'] +
        df_scaled['teammate_scaled'] * weights['teammate_score']
    )

    return df.sort_values('goat_index', ascending=False).reset_index(drop=True)
