import requests
import pandas as pd
from config import BASE_URL, PATH_CLUBS
import os

def fetch_clubs(competition_ids, season_id=''):
    # Betöltés, ha létezik
    if os.path.exists(PATH_CLUBS):
        clubs = pd.read_csv(PATH_CLUBS)
    else:
        clubs = pd.DataFrame()

    for comp_id in competition_ids:
        response = requests.get(f'{BASE_URL}/competitions/{comp_id}/clubs{season_id}')
        data = response.json()
        df = pd.DataFrame(data['clubs'])
        df['comp_id'] = data['id']
        df['seasonId'] = data['seasonId']
        df.rename(columns={'id': 'club_id', 'name': 'club_name'}, inplace=True)
        df = df[['seasonId', 'comp_id', 'club_id', 'club_name']]

        # Csak az új klubokat adjuk hozzá
        if not clubs.empty:
            df = df[~df['club_id'].isin(clubs['club_id'])]

        clubs = pd.concat([clubs, df], ignore_index=True)
        
        clubs = clubs.astype('str')
        clubs.drop_duplicates(keep='first', inplace=True)

    return clubs
