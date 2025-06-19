import pandas as pd
import numpy as np

driver_standings = pd.read_csv('driver_standings.csv')
drivers = pd.read_csv('drivers.csv')
races = pd.read_csv('races.csv')

def gini(array):
    array = np.array(array)
    if np.amin(array) < 0:
        array -= np.amin(array)  # Shift pozitív tartományba
    array += 1e-10  # Elkerüljük az osztást nullával
    array = np.sort(array)
    n = array.size
    cumulative = np.cumsum(array)
    return (2.0 * np.sum((np.arange(1, n + 1)) * array)) / (n * cumulative[-1]) - (n + 1) / n

# Egyesítés: driver_standings + races → évhez kötjük a pontokat
merged = pd.merge(driver_standings, races[['raceId', 'year']], on='raceId')

# Évszakokra aggregálás: minden szezonban az utolsó verseny driver standings-ét vizsgáljuk
latest_races = merged.groupby(['year'])['raceId'].max().reset_index()
final_standings = pd.merge(latest_races, merged, on=['year', 'raceId'])

# Gini index számítása szezononként
gini_per_year = final_standings.groupby('year')['points'].apply(gini).reset_index()
gini_per_year.columns = ['year', 'gini_index']

# Eredmény kiírása
print(gini_per_year.sort_values('year'))

#%% Viz
import matplotlib.pyplot as plt
plt.plot(gini_per_year['year'], gini_per_year['gini_index'])
plt.xticks(range(1950, 2025+1, 5), rotation=90)
plt.grid(True)
plt.show()