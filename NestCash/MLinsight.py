import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# --- 1. Data loading and preprocessing ---
def preprocess(df):
    df = df.copy()
    # Parse dates
    df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
    # Ensure numeric
    df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce')
    return df

# --- 2. Risk assessment ---
def risk_assessment(df, user_id, forecast_days=30):
    user_df = df[df['user_id'] == user_id].sort_values('datum')
    # Aggregate daily cumulative spending
    daily = (user_df.groupby(pd.to_datetime(user_df['datum']).dt.day)
             ['osszeg'].sum().cumsum().reset_index(name='cumsum'))
    X = daily[['datum']].apply(lambda x: x.dt.day) if hasattr(daily['datum'], 'dt') else daily[['datum']]
    X = daily[['datum']]
    X = np.array(daily.index).reshape(-1, 1)
    y = daily['cumsum'].values
    if len(y) < 2:
        return None
    model = LinearRegression().fit(X, y)
    pred_end = model.predict([[forecast_days]])[0]
    risk = pred_end < 0
    return pred_end, risk

# --- 3. Rolling averages ---
def compute_rolling(df, windows=[7,30,90]):
    df = df.sort_values('datum')
    for w in windows:
        df[f'roll_avg_{w}'] = df.groupby('user_id')['osszeg']\
                              .transform(lambda x: x.rolling(window=w, min_periods=1).mean())
    return df

# --- 4. Spending velocity ---
def compute_velocity(df, window=7):
    df = df.sort_values('datum')
    df['velocity'] = df.groupby('user_id')['osszeg']\
                       .transform(lambda x: x.rolling(window, min_periods=1).sum() / window)
    return df

# --- 5. Category Diversity Index ---
def category_diversity(df):
    div = df.groupby('user_id').apply(lambda x: x['kategoria'].nunique() / len(x))
    return div.rename('diversity_index')

# --- 6. Savings Rate Trend ---
def savings_rate_trend(df):
    df['ho'] = pd.to_datetime(df['datum']).dt.to_period('M')
    monthly = df.groupby(['user_id','ho'])['osszeg'].sum().reset_index()
    monthly_bevetel = df[df.osszeg > 0].groupby(['user_id', 'ho'])['osszeg']\
                                            .sum().reset_index()
    monthly_bevetel.rename(columns={'osszeg':'bevetel'}, inplace=True)
    
    monthly = pd.merge(monthly, monthly_bevetel, on=['user_id', 'ho'], how='left')
    monthly['savings_rate'] = monthly['osszeg'] / monthly['bevetel']
    
    monthly['trend'] = monthly.groupby('user_id')['savings_rate']\
                             .transform(lambda x: x.pct_change())
    return monthly

# --- 7. Fixed vs Variable Cost Ratio ---
def fixed_variable_ratio(df):
    ratios = {}
    for uid, group in df.groupby('user_id'):
        total = group[group['osszeg'] < 0]['osszeg'].sum()
        fixed = group[group['fix_koltseg'] == True]['osszeg'].sum()
        ratios[uid] = fixed / total if total != 0 else np.nan
    return pd.Series(ratios, name='fixed_ratio')

# --- 8. Benchmark comparison ---
def compare_to_profile(df, metric_series, profile_col='profil'):
    df_meta = df.drop_duplicates('user_id')[['user_id', profile_col]]
    metrics = metric_series.reset_index()
    metrics.columns = ['user_id', 'metric']
    merged = metrics.merge(df_meta, on='user_id')
    benchmark = merged.groupby(profile_col)['metric'].mean().rename('benchmark')
    merged = merged.merge(benchmark, left_on=profile_col, right_index=True)
    merged['vs_benchmark'] = merged['metric'] - merged['benchmark']
    return merged.set_index('user_id')[['metric','benchmark','vs_benchmark']]

# --- 9. ML model to predict improved savings ---
def train_save_model(df):
    # create features for each user
    df_proc = compute_rolling(df)
    div = category_diversity(df)
    fixed_ratio = fixed_variable_ratio(df)
    # assemble feature matrix
    feats = pd.DataFrame({
        'roll30': df_proc.groupby('user_id')['roll_avg_30'].last(),
        'roll7': df_proc.groupby('user_id')['roll_avg_7'].last(),
        'diversity': div,
        'fixed_ratio': fixed_ratio,
    })
    # target: assets or balance increase
    target = df.groupby('user_id')['assets'].last()
    X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train.fillna(0), y_train.fillna(0))
    preds = model.predict(X_test.fillna(0))
    rmse = np.sqrt(mean_squared_error(y_test.fillna(0), preds))
    return model

#%% --- Example usage ---
def MLinsight(df, user_id):
    risk, is_risk = risk_assessment(df, user_id)
    df_rolling = compute_rolling(df)
    div_index = category_diversity(df)
    savings_trend = savings_rate_trend(df)
    fv_ratio = fixed_variable_ratio(df)
    model = train_save_model(df)
    
    roll30_series = (
        df_rolling.sort_values('datum')
        .groupby('user_id')['roll_avg_30']
        .last()
    )
    
    comparison = compare_to_profile(df, roll30_series)
    
    
    if 'df' in locals():
        # 1) Kockázat
        pred_end, is_risk = risk_assessment(df, user_id)
        risk_msg = ("⚠️ Vigyázat! A hónap végén várhatóan mínuszba kerülsz."
                    if is_risk else
                    "✅ Jól állsz: várhatóan nem kerülsz mínuszba a hónap végén.")
        
        # 2) Mozgóátlagok
        roll7  = df_rolling.loc[df_rolling['user_id']==user_id, 'roll_avg_7'].iloc[-1]
        roll30 = df_rolling.loc[df_rolling['user_id']==user_id,'roll_avg_30'].iloc[-1]
        roll90 = df_rolling.loc[df_rolling['user_id']==user_id,'roll_avg_90'].iloc[-1]
        
        # 4) Kategória-diverzitás
        div    = div_index.loc[user_id]
        comparison_div = compare_to_profile(df, div_index)
        div_bm = comparison_div.loc[user_id, 'benchmark']
        
        # 5) Savings trend – az utolsó hónap %-os elmozdulása
        last_trends = savings_trend[savings_trend['user_id']==user_id].dropna(subset=['trend'])
        trend_pct = last_trends.iloc[-2]['trend'] * 100 if not last_trends.empty else 0
        trend_ch = (last_trends.iloc[-2]['savings_rate'] - last_trends.iloc[-3]['savings_rate'])

        # 6) Fixed vs Variable
        fv     = fv_ratio.loc[user_id]
        comparison_fv = compare_to_profile(df, fv_ratio)
        fvr_bm = comparison_fv.loc[user_id, 'benchmark']
        
        # 7) ML-predikció: mit javasol a modell?
        feats = pd.DataFrame({
            'roll30': [df_rolling[df_rolling['user_id']==user_id]['roll_avg_30'].iloc[-1]],
            'roll7': [df_rolling[df_rolling['user_id']==user_id]['roll_avg_7'].iloc[-1]],
            'diversity': [div],
            'fixed_ratio': [fv]
        })
        suggested_assets = model.predict(feats.fillna(0))[0]
        assets_now = float(df.groupby('user_id')['assets'].last()[user_id])
        
        
    return {'user_id': user_id,
            'risk_msg': risk_msg,
            'rolling_avg': {'roll7': roll7,
                            'roll30': roll30,
                            'roll90': roll90},
            'diversity': {'div_user': div, 'div_benchmark': div_bm},
            'savings_trend_pp': trend_ch,
            'fix_cost': {'fix_user': fv, 'fix_benchmark': fvr_bm},
            'suggested_assets': suggested_assets
            }