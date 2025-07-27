#%% Import, open data
import numpy as np
from mplsoccer import Sbopen
import pandas as pd 
from scipy.stats import poisson
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Open statsbomb event data
parser = Sbopen()
# All competitions
df_competitions = parser.competition()
# All games of Euro2024, Leverkusen and PSG
df_matches1 = parser.match(competition_id=55, season_id=282)
df_matches2 = parser.match(competition_id=9, season_id=281)
df_matches3 = parser.match(competition_id=7, season_id=235)

df_matches = pd.concat([df_matches1, df_matches2, df_matches3], ignore_index=True)

#%% Create dataframe
results_df = pd.DataFrame()

for match_id in df_matches.match_id.unique():
    try:
        # 1. Lekérdezzük a meccs eseményeit
        df, related, freeze, tactics = parser.event(match_id)
        shots = df[df.type_name == "Shot"]

        # 2. Paraméter: cutoff perc
        cutoff_minute = 45

        # 3. Meccs metaadatok
        match_info = df_matches[df_matches['match_id'] == match_id]
        home_team = match_info['home_team_name'].values[0]
        away_team = match_info['away_team_name'].values[0]
        
        # Debug információ
        print(f"Processing match: {home_team} vs {away_team} (ID: {match_id})")
        print(f"Total shots in match: {len(shots)}")

        # 4. Lövések a cutoff percig
        df_cutoff = shots[shots['minute'] <= cutoff_minute]
        print(f"Shots until minute {cutoff_minute}: {len(df_cutoff)}")

        # 5. Teljes meccs végeredménye (valódi gólok) - ELŐSZÖR SZÁMOLJUK KI
        all_goals = shots[shots['outcome_name'] == 'Goal']
        df_result = all_goals.groupby('team_name').size().reindex([home_team, away_team], fill_value=0)
        
        final_home_goals = int(df_result[home_team]) if home_team in df_result.index else 0
        final_away_goals = int(df_result[away_team]) if away_team in df_result.index else 0
        
        print(f"Final score: {home_team} {final_home_goals} - {final_away_goals} {away_team}")

        if df_cutoff.empty:
            # Ha nincs lövés a cutoff-ig
            xg_home_cutoff = 0.0
            xg_away_cutoff = 0.0
            goals_home_cutoff = 0
            goals_away_cutoff = 0
        else:
            # Csapatonkénti xG kiszámítása a cutoff-ig
            xg_cutoff = df_cutoff.groupby('team_name')['shot_statsbomb_xg'].sum()
            xg_home_cutoff = float(xg_cutoff.get(home_team, 0.0))
            xg_away_cutoff = float(xg_cutoff.get(away_team, 0.0))
            
            # Gólok kiszámítása a cutoff-ig
            goals_cutoff = df_cutoff[df_cutoff['outcome_name'] == 'Goal'].groupby('team_name').size()
            goals_home_cutoff = int(goals_cutoff.get(home_team, 0))
            goals_away_cutoff = int(goals_cutoff.get(away_team, 0))

        print(f"Until minute {cutoff_minute}: xG {xg_home_cutoff:.2f} - {xg_away_cutoff:.2f}, Goals {goals_home_cutoff} - {goals_away_cutoff}")

        # 6. Extrapolált xG -> várható gólok a hátralévő időre
        def estimate_future_goals(xg_cutoff, goals_cutoff, cutoff_min=30):
            if xg_cutoff == 0:
                return 0.0
            
            # Lineáris extrapoláció: ha 30 perc alatt xg_cutoff xG-t generáltak, 
            # akkor 90 perc alatt (xg_cutoff * 90/30) xG-t generálnának
            total_expected_xg = xg_cutoff * (90 / cutoff_min)
            
            # A hátralévő időre várt gólok = teljes várt xG - már elért gólok
            remaining_expected_goals = total_expected_xg - goals_cutoff
            
            return max(remaining_expected_goals, 0.0)

        adj_xg_home = estimate_future_goals(xg_home_cutoff, goals_home_cutoff, cutoff_minute)
        adj_xg_away = estimate_future_goals(xg_away_cutoff, goals_away_cutoff, cutoff_minute)
        
        print(f"Adjusted xG for remaining time: {adj_xg_home:.2f} - {adj_xg_away:.2f}")

        # 7. Poisson-modell
        def poisson_probs(xg_home, xg_away, max_goals=8):
            if xg_home == 0 and xg_away == 0:
                # Ha mindkét xG 0, akkor egyenlő valószínűségek
                return 1/3, 1/3, 1/3
            
            prob_matrix = np.zeros((max_goals+1, max_goals+1))
            for i in range(max_goals+1):
                for j in range(max_goals+1):
                    prob_matrix[i, j] = poisson.pmf(i, max(xg_home, 0.001)) * poisson.pmf(j, max(xg_away, 0.001))
            
            # Normalizálás
            prob_matrix = prob_matrix / np.sum(prob_matrix)
            
            home_win = np.sum(np.tril(prob_matrix, -1).T)  # i > j (home több gólt lő)
            draw = np.sum(np.diag(prob_matrix))            # i == j
            away_win = np.sum(np.triu(prob_matrix, 1))     # i < j (away több gólt lő)
            
            return home_win, draw, away_win

        pred_home_win, pred_draw, pred_away_win = poisson_probs(adj_xg_home, adj_xg_away)
        
        # 8. Legvalószínűbb eredmény
        probs = {'home': pred_home_win, 'draw': pred_draw, 'away': pred_away_win}
        pred_result = max(probs, key=probs.get)

        # 9. Tényleges eredmény
        if final_home_goals > final_away_goals:
            true_result = 'home'
        elif final_home_goals < final_away_goals:
            true_result = 'away'
        else:
            true_result = 'draw'

        correct = pred_result == true_result
        
        print(f"Prediction: {pred_result}, Actual: {true_result}, Correct: {correct}")
        print(f"Probabilities - Home: {pred_home_win:.3f}, Draw: {pred_draw:.3f}, Away: {pred_away_win:.3f}")
        print("-" * 50)

        # 10. Eredmények tárolása
        match_result = {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'xG_home': xg_home_cutoff,
            'xG_away': xg_away_cutoff,
            'goal_home_co': goals_home_cutoff,
            'goal_away_co': goals_away_cutoff,
            'adj_xG_home': adj_xg_home,
            'adj_xG_away': adj_xg_away,
            'pred_home_win': pred_home_win,
            'pred_draw': pred_draw,
            'pred_away_win': pred_away_win,
            'pred_result': pred_result,
            'goal_home': final_home_goals,
            'goal_away': final_away_goals,
            'true_result': true_result,
            'correct': correct
        }
        
        results_df = pd.concat([results_df, pd.DataFrame([match_result])], ignore_index=True)

    except Exception as e:
        print(f"Error processing match {match_id}: {str(e)}")
        continue

# Ellenőrizzük az eredményeket
print(f"\nTotal matches processed: {len(results_df)}")
print(f"Matches with non-zero xG: {len(results_df[(results_df['xG_home'] > 0) | (results_df['xG_away'] > 0)])}")
print(f"Matches with non-zero adjusted xG: {len(results_df[(results_df['adj_xG_home'] > 0) | (results_df['adj_xG_away'] > 0)])}")

# Statisztikák az xG értékekről
print(f"\nxG statistics (first {cutoff_minute} minutes):")
print(f"Home xG - Mean: {results_df['xG_home'].mean():.3f}, Max: {results_df['xG_home'].max():.3f}")
print(f"Away xG - Mean: {results_df['xG_away'].mean():.3f}, Max: {results_df['xG_away'].max():.3f}")

print(f"\nAdjusted xG statistics (for remaining time):")
print(f"Home adj_xG - Mean: {results_df['adj_xG_home'].mean():.3f}, Max: {results_df['adj_xG_home'].max():.3f}")
print(f"Away adj_xG - Mean: {results_df['adj_xG_away'].mean():.3f}, Max: {results_df['adj_xG_away'].max():.3f}")

# 11. Poisson-modell pontossága
accuracy_poisson = results_df['correct'].mean()
print(f"\nPontosság (Poisson-modell): {accuracy_poisson:.2%}")

# Eredmények eloszlása
print(f"\nPrediction distribution:")
print(results_df['pred_result'].value_counts())
print(f"\nActual result distribution:")
print(results_df['true_result'].value_counts())

# 12. Machine Learning modell (csak ha van elegendő adat)
if len(results_df) >= 10:  # Minimum 10 meccs kell
    X = results_df[['adj_xG_home', 'adj_xG_away', 'goal_home_co', 'goal_away_co']]
    y = results_df['true_result']

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # Ha kevés az adat, csökkentsük a fold számot
    n_splits = min(5, len(results_df) // 2)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)

    y_pred_cv = cross_val_predict(rf, X, y, cv=kf)

    results_df['pred_result_ml'] = y_pred_cv
    results_df['correct_ml'] = results_df['pred_result_ml'] == results_df['true_result']

    accuracy_ml = results_df['correct_ml'].mean()
    print(f"Pontosság (ML modellel, cross-validation): {accuracy_ml:.2%}")

    # 13. Confusion matrix és classification report
    print("\nConfusion Matrix (ML):")
    print(confusion_matrix(y, y_pred_cv))
    print("\nClassification Report (ML):")
    print(classification_report(y, y_pred_cv))
else:
    print(f"\nTúl kevés adat a ML modellhez ({len(results_df)} meccs)")

# Mentsük el az eredményeket
results_df.to_csv('match_predictions.csv', index=False)
print(f"\nEredmények mentve: match_predictions.csv")