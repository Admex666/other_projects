import requests
import pandas as pd
import time
import random
import os
from config import BASE_URL, PATH_PLAYERS

def fetch_players(clubs_df):
    # Betöltés, ha létezik
    if os.path.exists(PATH_PLAYERS):
        players = pd.read_csv(PATH_PLAYERS)
        existing_club_ids = set(players['club_id'].unique().astype(str))
        fetched_player_ids = set(players['player_id'])
    else:
        players = pd.DataFrame()
        existing_club_ids = set()
        fetched_player_ids = set()

    # Csak azok a klubok, amikhez még nincsenek játékosok
    unfetched_clubs = clubs_df[~clubs_df['club_id'].isin(existing_club_ids)]

    for i, row in unfetched_clubs.iterrows():
        club_id, seasonId = row['club_id'], row['seasonId']
        time.sleep(random.randint(0, 5))
        url_ending = f'?season_id={seasonId}' if seasonId != '2025' else ''
        response = requests.get(f'{BASE_URL}/clubs/{club_id}/players{url_ending}')
        data = response.json()

        if 'players' in data:
            if len(data['players']) != 0:
                df = pd.DataFrame(data['players'])
                df.rename(columns={'id': 'player_id', 'name': 'player_name'}, inplace=True)
                df['seasonId'] = seasonId
                df['club_id'] = club_id
                df = df[['seasonId', 'club_id', 'player_id', 'player_name',
                         'position', 'dateOfBirth', 'age', 'nationality',
                         'height', 'foot', 'joinedOn', 'signedFrom',
                         'contract', 'marketValue']]
    
                # Biztos, ami biztos: csak az új játékosok (ha adatduplikáció lenne)
                df = df[~df['player_id'].isin(fetched_player_ids)]
                players = pd.concat([players, df], ignore_index=True)
                
                players = players.astype('str')
                players.drop_duplicates(keep='first', inplace=True)
    
                print(f"Players added from club {club_id} ({row['club_name']}). Total players: {len(players)}")
            else:
                print(f"No players found for club {club_id} ({row['club_name']}).")
        else:
            print(f"No players found for club {club_id} ({row['club_name']}).")

    return players
