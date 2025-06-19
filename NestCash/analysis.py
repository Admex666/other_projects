import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from datetime import datetime

df_raw = pd.read_csv('szintetikus_tranzakciok.csv')

#%% Szokásalapú elemzés
mask = (df_raw.user_id==1) & (df_raw.osszeg < 0)
df = df_raw[mask].copy()

df['datum'] = pd.to_datetime(df['datum'])
df['osszeg_abs'] = df['osszeg'].abs()

# Jellemzők kiválasztása klaszterezéshez
features = df[['osszeg', 'nap_sorszam', 'osszeg_abs']].copy()

# Skálázás nélküli KMeans - baseline
kmeans = KMeans(n_clusters=3, random_state=0)
df['klaszter'] = kmeans.fit_predict(features[['osszeg_abs', 'nap_sorszam']])

# Vizualizáció
plt.scatter(df['nap_sorszam'], df['osszeg_abs'], c=df['klaszter'], cmap='viridis')
plt.xlabel('Nap a hónapban')
plt.ylabel('Költés (abs)')
plt.title('Költési klaszterek')
plt.show()

#%% Prediktív figyelmeztetés
df = df_raw.copy()
# Példa egy userre
user_id = 20
user_df = df[df['user_id'] == user_id].copy()

# Havi összesítés napokra bontva
daily = user_df.groupby('nap_sorszam')['osszeg'].sum().cumsum().reset_index()
X = daily[['nap_sorszam']]
y = daily['osszeg']

# Lineáris regresszió fit
model = LinearRegression()
model.fit(X, y)

# Predikció hónap végére
napok_szama = 30  # adott hónap hossza
pred = model.predict([[napok_szama]])[0]

print(f"Havi előrejelzett egyenleg a hónap végén: {pred:.2f} HUF")

if pred < 0:
    print("⚠️ Figyelem: Várhatóan mínuszba fogsz csúszni!")
