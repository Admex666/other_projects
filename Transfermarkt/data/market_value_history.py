import requests
import pandas as pd
from config import BASE_URL

def get_player_histMarketValue(tm_player_id):
    response = requests.get(f'{BASE_URL}/players/{tm_player_id}/market_value')
    player_data = response.json()

    if "marketValueHistory" in player_data:
        df = pd.DataFrame(player_data['marketValueHistory'])
        if 'marketValue' in df.columns:
            df['MV_mill'] = df['marketValue'] / 1000000
            df['player_id'] = tm_player_id
            df['date'] = pd.to_datetime(df['date']).dt.date
            return df[['player_id', 'age', 'date', 'clubId', 'clubName', 'MV_mill']]
        else:
            print(f"No market value for player {tm_player_id}")
            return pd.DataFrame()
    else:
        print(f"No market value history for player {tm_player_id}")
        return pd.DataFrame()
