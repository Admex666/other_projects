# teammate_comparison.py

import pandas as pd

def compare_teammates(results_df: pd.DataFrame, races_df: pd.DataFrame) -> pd.DataFrame:
    """
    Minden versenyzőre visszaadja, hogy hányszor győzte le (vagy veszített) csapattárssal szemben egy szezonban.

    Paraméterek:
        results_df (pd.DataFrame): normalizált pontokat tartalmazó results DataFrame
        races_df (pd.DataFrame): races.csv adatok (szezonokat tartalmaz)

    Visszatérés:
        pd.DataFrame: versenyzőnként összesített csapattárs elleni eredmények
    """

    # Összekapcsoljuk a szezon adatokat
    df = results_df.merge(races_df[['raceId', 'year']], on='raceId', how='left')

    # Szezon + csapat + versenyző szinten összesítjük a pontokat
    grouped = (
        df.groupby(['year', 'constructorId', 'driverId'])
          .agg(total_points=('normalized_points', 'sum'))
          .reset_index()
    )

    results = []

    # Végigmegyünk minden szezon-csapat kombináción
    for (year, constructor), group in grouped.groupby(['year', 'constructorId']):
        if len(group) < 2:
            continue  # csak 1 pilóta – nincs kivel összehasonlítani

        for idx, row in group.iterrows():
            driver_id = row['driverId']
            driver_points = row['total_points']

            # Csapattársak (akik nem ő maga)
            teammates = group[group['driverId'] != driver_id]

            for _, mate in teammates.iterrows():
                if driver_points > mate['total_points']:
                    result = 'win'
                elif driver_points < mate['total_points']:
                    result = 'loss'
                else:
                    result = 'draw'

                results.append({
                    'driverId': driver_id,
                    'year': year,
                    'constructorId': constructor,
                    'vs_driverId': mate['driverId'],
                    'result': result
                })

    results_df = pd.DataFrame(results)

    # Aggregáljuk: hány win/loss/draw
    summary = results_df.pivot_table(
        index='driverId',
        columns='result',
        aggfunc='size',
        fill_value=0
    ).reset_index()

    # Arányosítás
    summary['teammate_score'] = summary['win'] / (summary['win'] + summary['loss'] + 1e-9)

    return summary[['driverId', 'win', 'loss', 'draw', 'teammate_score']]
