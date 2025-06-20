#%% ML build df
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_validate, KFold, train_test_split
from sklearn.metrics import make_scorer, mean_absolute_error, r2_score

merged_GER = pd.read_csv('datafiles/merged_GER.csv')
merged_GER['mv_std_rel'] = merged_GER['mv_std'] / merged_GER['mv_1yr_ago']
merged_GER['mv_since_peak'] = (merged_GER['age_']+1) - merged_GER['mv_peak_age']

data = merged_GER[merged_GER['marketValue'].notna()].copy()
data.dropna(inplace=True)

data['pos_first'] = data.pos_.str.split(',').str[0]

target = 'mv_pct_change_1yr'
X = data.drop(columns=[target, 'marketValue', 'mv_pct_change_6mo', 'player_','pos_', 'PlayerFBref','born_', 'fbref_id', 'tm_id'])
y = data[target]

#%% ML: feature engineering, pipeline
state = 101
num_feats = [col for col in X.columns if X[col].dtype in [int,float]]
cat_feats = ['league_','pos_first','nation_']

numeric_transformer = Pipeline([
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline([
    ('ohe', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer([
    ('num', numeric_transformer, num_feats),
    ('cat', categorical_transformer, cat_feats)
])

pipe = Pipeline([
    ('prep', preprocessor),
    ('model', RandomForestRegressor(n_estimators=100, random_state=0))
])

X_train, X_test, y_train, y_test = train_test_split(
 X, y, test_size=0.25, random_state=state
)

pipe.fit(X_train, y_train)

y_pred = pipe.predict(X_test)

print("MAE:", mean_absolute_error(y_test, y_pred))
print("R²:", r2_score(y_test, y_pred))

cv = KFold(n_splits=5, shuffle=True, random_state=state)

scoring = {
    'mae': make_scorer(mean_absolute_error),
    'r2': make_scorer(r2_score)
}

cv_results = cross_validate(pipe, X, y, cv=cv, scoring=scoring,
                            return_train_score=True)
print(f"CV Mean MAE: {np.mean(cv_results['test_mae']):.4f} ± {np.std(cv_results['test_mae']):.4f}")
print(f"CV Mean R²: {np.mean(cv_results['test_r2']):.4f} ± {np.std(cv_results['test_r2']):.4f}")
errors = pd.DataFrame({'test': y_test, 'pred': y_pred, 'diff_pp': round(y_pred - y_test,2)})
print(errors)
print(f"Description of relative errors (pp):\n\n{abs(errors['diff_pp']).describe()}")

#%% Feature Importances
from sklearn.inspection import permutation_importance

res = permutation_importance(pipe, X_test, y_test, n_repeats=10, random_state=state, scoring='r2')
imp_mean = res.importances_mean
imp_std = res.importances_std

fi = pd.DataFrame({
    'feature': X.columns,
    'imp_mean': imp_mean,
    'imp_std': imp_std
}).sort_values('imp_mean', ascending=False).head(10)
print(fi)

#%%
import shap

# csak a modellre van szükség
model = pipe.named_steps['model']
X_sample = X_test.sample(min(100, len(X_test)), random_state=state)
X_transformed = preprocessor.transform(X_sample)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_transformed)

shap.summary_plot(shap_values, X_transformed, feature_names=pipe.named_steps['prep'].get_feature_names_out())

#%% Conclusion
import seaborn as sns
import matplotlib.pyplot as plt

sns.scatterplot(
    x=data['mv_std_rel'],
    y=data['mv_pct_change_1yr']
)
plt.xlabel("Relatív szórás (mv_std / mv_1yr_ago)")
plt.ylabel("Következő évi %-os változás")
plt.title("Piaci érték volatilitása vs. jövőbeli változás")
plt.show()

#%% Testing linreg
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# Célváltozó
y_target = data['mv_pct_change_1yr']

X = data[['mv_std_rel', 'age_', 'mv_since_peak']]
# Log
X['log_mv_since_peak'] = np.log1p(X['mv_since_peak'])
X = X.drop(columns='mv_since_peak')

# Train–test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_target, test_size=0.25, random_state=state
)

# Modell betanítása
model = LinearRegression()
model.fit(X_train, y_train)

# Előrejelzés
y_pred = model.predict(X_test)

from sklearn.model_selection import cross_validate, KFold

cv = KFold(n_splits=5, shuffle=True, random_state=state)

scoring = {
    'r2': 'r2',
    'mae': 'neg_mean_absolute_error'  # negatív, mert sklearn optimalizációra használja
}

cv_results = cross_validate(model, X, y_target, cv=cv, scoring=scoring)

print(f"CV R²: {cv_results['test_r2'].mean():.4f} ± {cv_results['test_r2'].std():.4f}")
print(f"CV MAE: {-cv_results['test_mae'].mean():.4f} ± {cv_results['test_mae'].std():.4f}")
print('\n')

# Koeficiensek
for feature, weight in zip(X.columns, model.coef_):
    print(f"{feature}: {weight:.4f}")
    
coef = model.coef_
coef_mv_std_rel, coef_age, coef_log_mv_since_peak = coef
intercept = model.intercept_

#%% Example prediction
CV_MAE = 0.21
# Values
MV_now_example = 20          # Market value (€M)

mv_std_rel = 0.5             # Relative std of market values
age = 33                     # Current age
#playing_time_mp = 30         # Played games in season
mv_since_peak = 10            # Years since ATH market value

# Calc
import numpy as np
## log 
log_mv_since_peak = np.log1p(mv_since_peak)

## Pred rel change
pred_change = (
    intercept
    + coef_mv_std_rel * mv_std_rel
    + coef_age * age
    + coef_log_mv_since_peak * log_mv_since_peak
)

pred_change_low = pred_change - CV_MAE
pred_change_high = pred_change + CV_MAE

print(f"Expected MV change in 1 year: {pred_change:.1%}")

# Pred future value
MV_next_year = MV_now_example * (1 + pred_change)
MV_next_year_low = MV_now_example * (1 + pred_change_low)
MV_next_year_high = MV_now_example * (1 + pred_change_high)
print(f"Expected market value in 1 year: €{MV_next_year:,.1f}M")
print(f'Expected MV in 1 year interval: €{MV_next_year_low:.0f}M - €{MV_next_year_high:.0f}M')

#%% Predictor: get data
from data.market_value_history import get_player_histMarketValue
from data.fetch_players import fetch_players
from config import PATH_CLUBS, PATH_PLAYERS

competition_ids = ['ES1', 'GB1', 'IT1', 'L1', 'NL1', 'FR1']
clubs = pd.read_csv(PATH_CLUBS)
players = pd.read_csv(PATH_PLAYERS)

#%%
"""
players_value_history = pd.DataFrame()
for i in players[371:].index:
    player_id = players.loc[i, 'player_id']
    player_vh = get_player_histMarketValue(player_id)
    
    players_value_history = pd.concat([players_value_history, player_vh], ignore_index=True)
    print(f'{i}/{len(players)} finished')
"""
# Save
PATH_valuehist = 'datafiles/players_value_history.csv'
if 'players_value_history' in locals():
    players_value_history.to_csv(PATH_valuehist, index=False)
else:
    players_value_history = pd.read_csv(PATH_valuehist)

#%% Predictor: predict
data = []
for player_id in players_value_history.player_id.unique():
    player_vh = players_value_history[players_value_history.player_id == player_id].reset_index(drop=True)
    player = players[players.player_id == player_id]
    
    if len(player_vh) < 3:
        print(f'Player {player_id} has less than 3 rows of values.')
    else:
        # relative std
        mv_std = player_vh['MV_mill'].std()
        marketValue = player['marketValue'].iloc[0] / 1_000_000
        mv_std_rel = mv_std / marketValue
        # age
        age = player['age'].iloc[0]
        # ages since peak
        mv_peak_age = player_vh.loc[player_vh['MV_mill'].idxmax(), 'age']
        mv_since_peak = age+1 - mv_peak_age
        log_mv_since_peak = np.log1p(mv_since_peak)
        
        # Predict
        CV_MAE = 0.21
        intercept = -0.9921134919756436
        coef_mv_std_rel = 2.971574715489453
        coef_age = 0.004485597374358357
        coef_log_mv_since_peak = -0.38106693840979206
        
        pred_change = (
            intercept
            + coef_mv_std_rel * mv_std_rel
            + coef_age * age
            + coef_log_mv_since_peak * log_mv_since_peak
        )
        pred_mv = round(marketValue * (1 + pred_change), 1)
        pred_change_low = pred_change - CV_MAE
        pred_change_high = pred_change + CV_MAE

        print(f"Expected MV change in 1 year: {pred_change:.1%}")
        
        # append
        data.append(
            {'player_id': player_id,
             'playerName': player['player_name'].iloc[0], 
             'clubName': clubs[
                 clubs.club_id == player['club_id'].iloc[0]]['club_name'].iloc[0],
             'age': age,
             'marketVal': marketValue,
             'mv_std_rel': mv_std_rel,
             'mv_since_peak': mv_since_peak,
             'pred_change_low': pred_change_low,
             'pred_change_high': pred_change_high,
             'pred_change': pred_change,
             'pred_mv': pred_mv}
                    )

df_pred = pd.DataFrame(data)

#%% Random forest pred
X_input = df_pred[['mv_std_rel', 'mv_since_peak', 'age']]
X_input['log_mv_since_peak'] = np.log1p(X_input['mv_since_peak'])
X_input = X_input.drop(columns='mv_since_peak')
X_input.rename(columns= {'age': 'age_'}, inplace=True)

df_pred['pred_change_RF'] = pipe.predict(X_input)

#%% Compare
df_pred[['pred_change', 'pred_change_RF']].describe()

df_pred[['playerName', 'clubName', 'age', 'marketVal', 'pred_change', 'pred_change_RF']
        ].sort_values(by='pred_change_RF', ascending=False).to_excel('pred_change.xlsx', index=False)