import pandas as pd
import numpy as np

lap_times = pd.read_csv('lap_times.csv')
races = pd.read_csv('races.csv')

merged = pd.merge(lap_times, races,
                  how="left", on="raceId")

print(merged.head())

gp = 'Hungarian Grand Prix'
merged_circuit = merged[merged.name == gp]
years = np.sort(merged_circuit.year.unique())

race_lap_times = pd.DataFrame()
race_lap_times.index = years
for year in years:
    merged_circuit_year = merged_circuit[merged_circuit.year == year]
    median_lap_time_ms = merged_circuit_year.milliseconds.median()
    fastest_lap_time_ms = merged_circuit_year.milliseconds.min()
    # add to df
    race_lap_times.loc[year, 'median_lap_time'] = median_lap_time_ms
    race_lap_times.loc[year, 'fastest_lap'] = fastest_lap_time_ms

#%%
import matplotlib.pyplot as plt

plt.plot(race_lap_times.index, race_lap_times['median_lap_time'])
plt.title(f'Median lap times trend of {gp}')
plt.show()

plt.plot(race_lap_times.index, race_lap_times['fastest_lap'])
plt.title(f'Fastest lap times trend of {gp}')
plt.show()