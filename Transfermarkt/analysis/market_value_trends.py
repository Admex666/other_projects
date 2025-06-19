import pandas as pd
import numpy as np
from data.market_value_history import get_player_histMarketValue
from sklearn.linear_model import LinearRegression

def enrich_with_mv_trends(df):
    df = df.copy()
    df = df[df['league_'] == 'GER-Bundesliga']  # vagy paraméterezve
    for i in df.index:
        try:
            tm_id = int(df.loc[i, 'tm_id'])
            mv_df = get_player_histMarketValue(tm_id)
            if mv_df.empty:
                continue
            mv_df['date'] = pd.to_datetime(mv_df['date'])
            mv_df.sort_values('date', inplace=True)
            mv_latest = mv_df.iloc[-1]['MV_mill']
            mv_1yr_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-06-01')]['MV_mill'].max()
            mv_6mo_ago = mv_df[mv_df['date'] < pd.Timestamp('2024-12-01')]['MV_mill'].max()
            mv_pct_change_1yr = (mv_latest - mv_1yr_ago) / mv_1yr_ago if mv_1yr_ago else np.nan
            mv_pct_change_6mo = (mv_latest - mv_6mo_ago) / mv_6mo_ago if mv_6mo_ago else np.nan
            recent_df = mv_df[mv_df['date'] >= pd.Timestamp('2022-01-01')]
            recent_df['date_num'] = (recent_df['date'] - pd.Timestamp('1970-01-01')).dt.days
            X = recent_df[['date_num']]
            y = recent_df['MV_mill']
            model = LinearRegression().fit(X, y) if len(X) >= 2 else None
            mv_trend_slope = model.coef_[0] if model else np.nan
            mv_last_diff = mv_df['MV_mill'].iloc[-1] - mv_df['MV_mill'].iloc[-2] if len(mv_df) >= 2 else np.nan
            mv_std = mv_df['MV_mill'].std()
            mv_min = mv_df['MV_mill'].min()
            mv_max = mv_df['MV_mill'].max()
            mv_peak_age = mv_df.loc[mv_df['MV_mill'].idxmax(), 'age']
            df.loc[i, ['marketValue', 'mv_1yr_ago', 'mv_6mo_ago', 'mv_pct_change_1yr',
                       'mv_pct_change_6mo', 'mv_trend_slope', 'mv_last_diff',
                       'mv_std', 'mv_min', 'mv_max', 'mv_peak_age']] = [
                mv_latest, mv_1yr_ago, mv_6mo_ago, mv_pct_change_1yr,
                mv_pct_change_6mo, mv_trend_slope, mv_last_diff,
                mv_std, mv_min, mv_max, mv_peak_age
            ]
        except Exception as e:
            print(f"⚠️ Error at {i}: {e}")
            continue
    return df
