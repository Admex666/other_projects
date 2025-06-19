import pandas as pd
from config import PATH_PLAYERS, PATH_MAPPING
from utils.io_utils import save_df
from data.market_value_history import get_player_histMarketValue
import soccerdata as sd

def build_merged_df(season='2425', league_filter='GER-Bundesliga', save_path='datafiles/merged_GER.csv'):
    # 1. Játékosok betöltése
    players = pd.read_csv(PATH_PLAYERS)
    
    # 2. Mapping betöltése
    mapping = pd.read_csv(PATH_MAPPING)
    
    # 3. FBref statisztikák letöltése
    fb = sd.FBref(leagues='Big 5 European Leagues Combined', seasons=[season])
    player_stats = fb.read_player_season_stats(stat_type='standard')
    
    ps = player_stats.reset_index()
    ps.columns = ['_'.join(col).strip() for col in ps.columns.values]
    
    # 4. Összefűzés: FBref <-> Mapping
    merged = pd.merge(ps, mapping[['PlayerFBref','fbref_id','tm_id']],
                      left_on='player_', right_on='PlayerFBref',
                      how='inner')
    
    # 5. Összefűzés: mapping <-> piaci értékek
    merged = pd.merge(merged, players[['player_id', 'marketValue']], 
                      how='left', left_on='tm_id', right_on='player_id')
    
    print(f"[INFO] Merged shape: {merged.shape}")
    print(f"[INFO] Missing FBref IDs: {merged['fbref_id'].isna().sum()}")
    print(f"[INFO] Missing Market Values: {merged['marketValue'].isna().sum()}")

    # 6. Csak adott liga
    merged = merged[merged['league_'] == league_filter].copy()
    
    # 7. Historikus értékek kalkulációja
    from sklearn.linear_model import LinearRegression
    import numpy as np
    import pandas as pd

    for i in merged.index:
        tm_id = int(merged.loc[i, 'tm_id'])
        mv_df = get_player_histMarketValue(tm_id)

        if mv_df.empty:
            print(f"[WARN] No MV history for {i} ({tm_id})")
            continue
        
        mv_df['date'] = pd.to_datetime(mv_df['date'])
        mv_df = mv_df.sort_values('date').reset_index(drop=True)

        mv_latest = mv_df.iloc[-1]['MV_mill']
        mv_1yr_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-06-01')]['MV_mill'].max()
        mv_6mo_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-12-01')]['MV_mill'].max()

        mv_pct_change_1yr = (mv_latest - mv_1yr_ago) / mv_1yr_ago if mv_1yr_ago else np.nan
        mv_pct_change_6mo = (mv_latest - mv_6mo_ago) / mv_6mo_ago if mv_6mo_ago else np.nan

        recent_df = mv_df[mv_df['date'] >= pd.Timestamp('2022-01-01')].copy()
        recent_df['date_num'] = (recent_df['date'] - pd.Timestamp('1970-01-01')).dt.days

        X = recent_df.dropna()[['date_num']]
        y = recent_df.dropna()['MV_mill']

        if len(X) >= 2:
            model = LinearRegression().fit(X, y)
            mv_trend_slope = model.coef_[0]
        else:
            mv_trend_slope = np.nan

        mv_last_diff = mv_df['MV_mill'].iloc[-1] - mv_df['MV_mill'].iloc[-2] if len(mv_df) >= 2 else np.nan
        mv_std = mv_df['MV_mill'].std()
        mv_min = mv_df['MV_mill'].min()
        mv_max = mv_df['MV_mill'].max()
        mv_peak_age = mv_df.loc[mv_df['MV_mill'].idxmax(), 'age']

        mv_values = [mv_latest, mv_1yr_ago, mv_6mo_ago, mv_pct_change_1yr,
                     mv_pct_change_6mo, mv_trend_slope, mv_last_diff,
                     mv_std, mv_min, mv_max, mv_peak_age]

        merged.loc[i, ['marketValue', 'mv_1yr_ago', 'mv_6mo_ago', 'mv_pct_change_1yr',
                       'mv_pct_change_6mo', 'mv_trend_slope', 'mv_last_diff',
                       'mv_std', 'mv_min', 'mv_max', 'mv_peak_age']] = mv_values

    # 8. Deduplikálás és mentés
    merged.drop_duplicates(subset='player_', keep=False, inplace=True)
    
    return merged