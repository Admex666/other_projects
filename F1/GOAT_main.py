# main.py

from GOAT.load_data import load_all_data
from GOAT.normalize_points import apply_normalized_points
from GOAT.metrics import calculate_driver_metrics
from GOAT.season_context import compute_season_context
from GOAT.teammate_comparison import compare_teammates
from GOAT.goat_index import calculate_goat_index

data = load_all_data('datafiles')
# Normalizálás
results_df = apply_normalized_points(data['results'])
# Alapmetrikák
driver_metrics = calculate_driver_metrics(results_df, data['qualifying'])
# Szezonkontextus
season_context = compute_season_context(results_df, data['races'])
teammate_df = compare_teammates(results_df, data['races'])
goat_df = calculate_goat_index(driver_metrics, teammate_df)
goat_df = goat_df.merge(data['drivers'][['driverId', 'surname', 'forename']], on='driverId', how='left')

print(goat_df[['forename', 'surname', 'goat_index', 'races', 'wins']].head(10))
