#%%
from data.fetch_clubs import fetch_clubs
from data.fetch_players import fetch_players
from mapping.mapper import load_mapping, is_in_mapping
from utils.io_utils import save_df
from analysis.build_merged import build_merged_df
from analysis.market_value_trends import enrich_with_mv_trends
from modeling.train_model import train_and_evaluate_model
from modeling.predict_single import predict_future_value
from config import PATH_CLUBS, PATH_PLAYERS, PATH_MERGED
import pandas as pd

def main():
    # 1. Klubok és játékosok lekérése
    competition_ids = ['ES1', 'GB1', 'IT1', 'L1', 'NL1', 'FR1']
    clubs = fetch_clubs(competition_ids)
    players = pd.read_csv(PATH_PLAYERS)
    #players = fetch_players(clubs)

    # 2. Mapping + mentés
    mapping = load_mapping()
    players['isInMapping'] = players['player_id'].apply(lambda pid: is_in_mapping(mapping, pid))
    save_df(clubs, PATH_CLUBS)
    save_df(players, PATH_PLAYERS)

    # 3. Merge: FBref + Transfermarkt
    #merged = build_merged_df(mapping, players)
    merged = pd.read_csv(PATH_MERGED)

    # 4. Historic trendek hozzáadása
    #merged = enrich_with_mv_trends(merged)

    # 5. Modellépítés és kiértékelés
    model, preprocessor, test_data = train_and_evaluate_model(merged)

    # 6. Példapredikció
    predict_future_value(model, preprocessor, merged)

if __name__ == '__main__':
    main()

#%% 
import soccerdata as sd

# Példa 3 szezonra + top 5 liga
fb = sd.FBref(leagues='Big 5 European Leagues Combined', seasons=['2425'])
player_stats = fb.read_player_season_stats(stat_type='standard')
ps = player_stats.reset_index()
ps.columns = ['_'.join(col).strip() for col in ps.columns.values]

merged = pd.merge(ps, mapping[['PlayerFBref','fbref_id','tm_id']],
                  left_on='player_', right_on='PlayerFBref',
                  how='inner')
print(f"Number of NaNs (fbref-TM): {len(merged[merged['fbref_id'].isna()])}")
merged = pd.merge(merged, players[['player_id', 'marketValue']], 
                  how='left', left_on='tm_id', right_on='player_id')
print(f"Number of NaNs (marketval): {len(merged[merged['marketValue'].isna()])}")
"""
#%% Add historic market value trends

from sklearn.linear_model import LinearRegression
merged_GER = merged[merged.league_ == 'GER-Bundesliga'].copy()

for i in merged_GER.loc[1272:].index:
    tm_id = int(merged_GER.loc[i, 'tm_id'])
    mv_df = get_player_histMarketValue(tm_id)
    
    #time.sleep(random.randint(10, 20))
    
    if mv_df.empty:
        print(f'Values not found for {i}')
        continue
    else:
        print(f'Values found for {i}')
    
        mv_df['date'] = pd.to_datetime(mv_df['date'])
        mv_df = mv_df.sort_values('date').reset_index(drop=True)
        
        # A legutóbbi értékek (prediction előtti állapot):
        mv_latest = mv_df.iloc[-1]['MV_mill']
        mv_1yr_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-06-01')]['MV_mill'].max()
        mv_6mo_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-12-01')]['MV_mill'].max()
        
        # Relatív változások:
        mv_pct_change_1yr = (mv_latest - mv_1yr_ago) / mv_1yr_ago if mv_1yr_ago else np.nan
        mv_pct_change_6mo = (mv_latest - mv_6mo_ago) / mv_6mo_ago if mv_6mo_ago else np.nan
        
        # Csak az utolsó 3 év adatait nézzük (pl. 2022–2025)
        recent_df = mv_df[mv_df['date'] >= pd.Timestamp('2022-01-01')].copy()
        
        # Dátumokat számmá alakítjuk (napok 1970 óta)
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
                  mv_pct_change_6mo, mv_trend_slope, mv_last_diff, mv_std, mv_min, 
                  mv_max, mv_peak_age]
        
        merged_GER.loc[i, ['marketValue', 'mv_1yr_ago', 'mv_6mo_ago', 'mv_pct_change_1yr', 
                           'mv_pct_change_6mo', 'mv_trend_slope', 'mv_last_diff', 'mv_std', 
                           'mv_min', 'mv_max', 'mv_peak_age']] = mv_values

merged_GER.drop_duplicates(subset='player_', keep=False, inplace=True)
save_df(merged_GER, 'datafiles/merged_GER.csv')
"""    
