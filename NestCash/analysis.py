import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from datetime import datetime

df_raw = pd.read_csv('szintetikus_tranzakciok.csv')
df = df_raw.copy()

#%% Szokásalapú elemzés
mask = (df_raw.user_id==1) & (df_raw.osszeg < 0) & (df_raw.bev_kiad_tipus != "szukseglet")
df_f = df_raw[mask].copy()

df_f['datum'] = pd.to_datetime(df_f['datum'])
df_f['osszeg_abs'] = df_f['osszeg'].abs()

# Jellemzők kiválasztása klaszterezéshez
features = df_f[['osszeg', 'nap_sorszam', 'osszeg_abs']].copy()

# Skálázás nélküli KMeans - baseline
kmeans = KMeans(n_clusters=3, random_state=0)
df_f['klaszter'] = kmeans.fit_predict(features[['osszeg_abs', 'nap_sorszam']])

# Vizualizáció
plt.scatter(df_f['nap_sorszam'], df_f['osszeg_abs'], c=df_f['klaszter'], cmap='viridis')
plt.xlabel('Nap a hónapban')
plt.ylabel('Költés (abs)')
plt.title('Költési klaszterek')
plt.show()

#%% Prediktív figyelmeztetés
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

print(f"{napok_szama} nap múlva előrejelzett egyenleg: {pred:.2f} HUF")

if pred < 0:
    print("⚠️ Figyelem: Várhatóan mínuszba fogsz csúszni!")

#%% Spórolási javaslatok
# Kategória szerinti összegzés
kategoriak = user_df.groupby('kategoria')['osszeg'].sum().sort_values()

# Csak "luxus" típusokat nézünk
luxus_df = user_df[user_df['tipus'].isin(['vagy', 'impulzus'])]
luxus_kat = luxus_df.groupby('kategoria')['osszeg'].sum().sort_values()

# minél nagyobb a luxus kategória költés, annál nagyobb a spórolási potenciál
print("💰 Lehetséges spórolási pontok (luxus kategóriák, összes költés):")
print(luxus_kat)

#%% Szokások változása havonta
user_df['honap'] = pd.to_datetime(df['honap'], errors='coerce')
havi_kolt = user_df.groupby(['honap', 'kategoria'])['osszeg'].sum().abs().unstack().fillna(0)

# Egyszerű változás mutatása pl. "mozi" kategóriában
havi_kolt['mozi'].plot(kind='line', marker='o')
plt.title('Mozi költés havonta')
plt.ylabel('Összeg (HUF)')
plt.xlabel('Hónap')
plt.show()

#%% Napi átlagos költés
user_df = df[df['user_id'] == user_id]

# Csak kiadások
kiadasok = user_df[user_df['osszeg'] < 0]

# Egyedi napok számolása
egyedi_napok = kiadasok['datum'].nunique()
atlag_napi_koltes = kiadasok['osszeg'].sum() / egyedi_napok

print(f"📅 Átlagos napi költés: {atlag_napi_koltes:.2f} HUF")

# Kategória szerinti szórás
szoras_kategoria = user_df.groupby('kategoria')['osszeg'].std().sort_values(ascending=False)

print("📊 Kategóriánkénti költésszórás:")
print(szoras_kategoria)

#%% Spórolási potenciál
ossz_kiadas = -kiadasok['osszeg'].sum()
luxus_kiadas = -user_df[(user_df['tipus'] == 'vagy') & (user_df['osszeg'] < 0)]['osszeg'].sum()

sporolasi_potencial = luxus_kiadas / ossz_kiadas if ossz_kiadas > 0 else 0

print(f"Spórolási potenciál arány (luxus/össz): {sporolasi_potencial:.2%}")

#%% Havi cél egyenleg
havi_cel = 300_000

# Havi költés vs. bevétel (feltételezve, hogy nincs explicit "bevétel" típus még)
havi_adatok = user_df[pd.to_datetime(user_df['datum']).dt.month == datetime.now().month]
egyenleg = havi_adatok['assets'].to_list()[-1]

celhaladas = min(max(egyenleg / havi_cel, 0), 1)

print(f"🎯 Havi cél teljesülés: {celhaladas * 100:.1f}%")

#%%
from sklearn.metrics import mean_squared_error

# Tegyük fel, hogy vizsgáljuk 2024-08 hónapot
honap = '2024-08'
user_havi = user_df[user_df['datum'].str[:7] == honap]

# Napi kumulált költés
daily = user_havi.groupby('nap_sorszam')['osszeg'].sum().cumsum().reset_index()
X = daily[['nap_sorszam']]
y = daily['osszeg']

# Modell betanítása és előrejelzés
model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)

rmse = np.sqrt(mean_squared_error(y, y_pred))

print(f"📉 RMSE (predikció vs. valós költés): {rmse:.2f} HUF")
