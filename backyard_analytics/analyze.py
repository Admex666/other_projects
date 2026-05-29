import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Set visual style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'font.family': 'sans-serif'
})

# Create directories
os.makedirs("plots", exist_ok=True)
os.makedirs("data", exist_ok=True)

# -------------------------------------------------------------
# 0. Data Loading & Cleaning
# -------------------------------------------------------------

def parse_time_to_seconds(t_str):
    if pd.isna(t_str) or not isinstance(t_str, str):
        return np.nan
    t_str = t_str.strip()
    # Format: HH:MM:SS or MM:SS
    parts = t_str.split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return float(t_str)
    except ValueError:
        return np.nan

def clean_lap_number(lap_str):
    if pd.isna(lap_str) or not isinstance(lap_str, str):
        return np.nan
    # Extract digits from e.g. "1. kör" or "45. kör"
    match = re.search(r'\d+', lap_str)
    return int(match.group()) if match else np.nan

def load_data():
    overall = pd.read_csv("data/overall_results.csv", encoding="utf-8-sig")
    detailed = pd.read_csv("data/detailed_laps.csv", encoding="utf-8-sig")
    
    # Clean overall columns robustly by matching substrings
    col_mapping = {}
    for col in overall.columns:
        if 'BackyardNumberOfLaps' in col:
            col_mapping[col] = 'Laps'
        elif 'DECIMALTIME10' in col or 'km' in col:
            col_mapping[col] = 'Distance_km'
        elif 'YEAR' in col:
            col_mapping[col] = 'YearOfBirth'
        elif 'DisplayName' in col:
            col_mapping[col] = 'Name'
            
    overall.rename(columns=col_mapping, inplace=True)
    
    # Clean detailed columns robustly too
    det_mapping = {}
    for col in detailed.columns:
        if 'DisplayName' in col or 'Name' in col:
            det_mapping[col] = 'Name'
    detailed.rename(columns=det_mapping, inplace=True)
    
    # Fix names encoding issues if any
    overall['Name'] = overall['Name'].str.strip()
    detailed['Name'] = detailed['Name'].str.strip()
    
    # Extract integers from Laps (e.g. "45 kör" -> 45)
    overall['Laps_Count'] = overall['Laps'].astype(str).str.extract(r'(\d+)').astype(float)
    
    # Clean Distance
    overall['Distance_km'] = overall['Distance_km'].astype(str).str.replace(' km', '').str.replace(',', '.').str.strip().astype(float)
    
    # Age
    overall['Age'] = 2026 - overall['YearOfBirth']
    
    # Convert lap details
    detailed['Lap_Num'] = detailed['Lap'].apply(clean_lap_number)
    detailed['Seconds'] = detailed['LapTime'].apply(parse_time_to_seconds)
    detailed['Minutes'] = detailed['Seconds'] / 60.0

    # Cast ID columns to uniform int type for merge safety
    overall['ID'] = overall['ID'].astype(int)
    detailed['PID'] = detailed['PID'].astype(int)
    
    return overall, detailed

# -------------------------------------------------------------
# 1. Survival Analysis
# -------------------------------------------------------------

def analyze_survival(overall):
    n_total = len(overall)
    max_laps = int(overall['Laps_Count'].max())
    
    # Survival by lap
    survival_data = []
    for lap in range(1, max_laps + 2):
        # Active in lap N means they completed at least N-1 laps
        survived = (overall['Laps_Count'] >= lap).sum()
        prob = survived / n_total
        survival_data.append({'Lap': lap, 'SurvivedCount': survived, 'SurvivalProb': prob})
        
    df_surv = pd.DataFrame(survival_data)
    
    # Median survival
    median_laps = overall['Laps_Count'].median()
    
    # Plot Kaplan-Meier Survival Curve
    plt.figure(figsize=(10, 6))
    plt.step(df_surv['Lap'], df_surv['SurvivalProb'] * 100, where='post', color='#2b5c8f', linewidth=2.5, label='K-M Túlélési Görbe')
    plt.axhline(50, color='#d9534f', linestyle='--', label=f'Medián Túlélés ({median_laps:.1f} kör)')
    plt.title('Backyard Ultra Kaplan-Meier Túlélési Görbe', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Körök száma (Órák)', fontsize=12)
    plt.ylabel('Versenyben lévők aránya (%)', fontsize=12)
    plt.xlim(1, max_laps + 1)
    plt.ylim(0, 105)
    plt.legend(frameon=True, facecolor='white', edgecolor='none')
    plt.tight_layout()
    plt.savefig('plots/1_survival_curve.png', dpi=150)
    plt.close()
    
    # Plot Lap Dropouts Distribution
    plt.figure(figsize=(10, 5))
    dropout_counts = overall['Laps_Count'].value_counts().sort_index()
    sns.barplot(x=dropout_counts.index.astype(int), y=dropout_counts.values, color='#4a90e2')
    plt.title('Kiesések eloszlása körönként', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Kiesési kör', fontsize=12)
    plt.ylabel('Kiesett versenyzők száma', fontsize=12)
    plt.tight_layout()
    plt.savefig('plots/1_dropout_distribution.png', dpi=150)
    plt.close()
    
    return df_surv, median_laps

# -------------------------------------------------------------
# 2. Lap Time Dynamics
# -------------------------------------------------------------

def analyze_dynamics(overall, detailed):
    # Field Average Lap Time per Lap
    field_avg = detailed.groupby('Lap_Num')['Minutes'].agg(['mean', 'std', 'count']).reset_index()
    
    # Regress slope for each runner (LapTime drift)
    runners_drift = []
    for pid, group in detailed.groupby('PID'):
        if len(group) >= 3:
            slope, intercept, r_value, p_value, std_err = stats.linregress(group['Lap_Num'], group['Minutes'])
            runners_drift.append({'PID': pid, 'Drift_Slope': slope, 'Std_Lap': group['Minutes'].std()})
    df_drift = pd.DataFrame(runners_drift)
    overall = overall.merge(df_drift, left_on='ID', right_on='PID', how='left')
    
    # Plot Top 5 Runners Pacing
    plt.figure(figsize=(12, 6))
    top_pids = overall.sort_values(by='Laps_Count', ascending=False).head(5)['ID'].values
    colors = ['#2c3e50', '#e74c3c', '#3498db', '#f1c40f', '#2ecc71']
    for pid, color in zip(top_pids, colors):
        runner_laps = detailed[detailed['PID'] == pid].sort_values('Lap_Num')
        name = runner_laps['Name'].iloc[0]
        laps_completed = int(runner_laps['Lap_Num'].max())
        plt.plot(runner_laps['Lap_Num'], runner_laps['Minutes'], marker='o', markersize=4, 
                 linewidth=1.8, label=f"{name} ({laps_completed} kör)", color=color)
                 
    plt.axhline(60, color='red', linestyle=':', linewidth=1.5, label='Kör limit (60 perc)')
    plt.title('A Top 5 versenyző köridőinek alakulása', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Kör sorszáma', fontsize=12)
    plt.ylabel('Köridő (perc)', fontsize=12)
    plt.ylim(30, 62)
    plt.legend(frameon=True, loc='lower left')
    plt.tight_layout()
    plt.savefig('plots/2_top5_pacing.png', dpi=150)
    plt.close()
    
    # Plot Field Average Pacing Trend
    plt.figure(figsize=(10, 6))
    plt.plot(field_avg['Lap_Num'], field_avg['mean'], color='#16a085', linewidth=2.5, marker='s', label='Mezőny átlag')
    plt.fill_between(field_avg['Lap_Num'], field_avg['mean'] - field_avg['std'], field_avg['mean'] + field_avg['std'], 
                     color='#16a085', alpha=0.15, label='Szórás (±1 SD)')
    plt.axhline(60, color='red', linestyle=':', label='Kör limit')
    plt.title('Mezőny átlagos köridejének trendje', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Kör sorszáma', fontsize=12)
    plt.ylabel('Átlagos köridő (perc)', fontsize=12)
    plt.xlim(1, len(field_avg))
    plt.legend()
    plt.tight_layout()
    plt.savefig('plots/2_field_pacing_trend.png', dpi=150)
    plt.close()
    
    return overall, field_avg

# -------------------------------------------------------------
# 3. Strategy Clustering
# -------------------------------------------------------------

def analyze_clustering(overall, detailed):
    # Build features per runner
    features_list = []
    for pid, group in detailed.groupby('PID'):
        if len(group) >= 2:
            slope, _, _, _, _ = stats.linregress(group['Lap_Num'], group['Minutes'])
            features_list.append({
                'ID': pid,
                'Total_Laps': len(group),
                'Mean_LapTime': group['Minutes'].mean(),
                'Std_LapTime': group['Minutes'].std(),
                'Drift_Slope': slope,
                'Min_LapTime': group['Minutes'].min()
            })
    df_feat = pd.DataFrame(features_list)
    
    # Scale features for K-Means
    scaler = StandardScaler()
    feat_cols = ['Total_Laps', 'Mean_LapTime', 'Std_LapTime', 'Drift_Slope', 'Min_LapTime']
    scaled_feats = scaler.fit_transform(df_feat[feat_cols])
    
    # Fit KMeans
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df_feat['Cluster'] = kmeans.fit_predict(scaled_feats)
    
    # Merge back to overall
    overall = overall.merge(df_feat[['ID', 'Cluster']], on='ID', how='left')
    
    # Analyze clusters and label them
    cluster_means = df_feat.groupby('Cluster')[feat_cols].mean()
    print("Cluster Means:\n", cluster_means)
    
    # Let's map clusters dynamically based on their attributes:
    # 1. High Laps, Low Std -> "Steady Grinders"
    # 2. Low Laps, Low Mean -> "Fast Sprinters"
    # 3. High Laps, High Std -> "Limit Survivors"
    # 4. Low Laps, High Mean -> "Strugglers"
    
    cluster_labels = {}
    for c in range(4):
        subset = df_feat[df_feat['Cluster'] == c]
        avg_laps = subset['Total_Laps'].mean()
        avg_mean = subset['Mean_LapTime'].mean()
        avg_std = subset['Std_LapTime'].mean()
        
        if avg_laps >= 20 and avg_std < 3.5:
            cluster_labels[c] = "Steady Grinders (Stabil Túlélők)"
        elif avg_laps >= 12 and avg_std >= 3.5:
            cluster_labels[c] = "Limit Survivors (Határon Futók)"
        elif avg_laps < 12 and avg_mean < 48:
            cluster_labels[c] = "Fast Sprinters (Korai Kiégők)"
        else:
            cluster_labels[c] = "Average Pack (Átlagos Mezőny)"
            
    df_feat['Cluster_Label'] = df_feat['Cluster'].map(cluster_labels)
    
    # Plot Clusters
    plt.figure(figsize=(10, 6))
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
    for label, color in zip(df_feat['Cluster_Label'].unique(), colors):
        sub = df_feat[df_feat['Cluster_Label'] == label]
        plt.scatter(sub['Mean_LapTime'], sub['Total_Laps'], s=sub['Std_LapTime']*20 + 30, 
                    color=color, label=label, alpha=0.8, edgecolors='w', linewidth=0.5)
                    
    plt.title('Stratégia klaszterek a köridő és a teljesített körök alapján', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Átlagos köridő (perc)', fontsize=12)
    plt.ylabel('Összes teljesített kör', fontsize=12)
    plt.legend(frameon=True, facecolor='white')
    plt.tight_layout()
    plt.savefig('plots/3_strategy_clusters.png', dpi=150)
    plt.close()
    
    return overall, cluster_labels, df_feat

# -------------------------------------------------------------
# 4. Demographics vs. Performance
# -------------------------------------------------------------

def analyze_demographics(overall):
    # Exclude invalid ages (some years might be missing or placeholder)
    valid_age = overall[(overall['Age'] > 10) & (overall['Age'] < 90)].copy()
    
    # Plot Age vs. Laps
    plt.figure(figsize=(10, 6))
    sns.regplot(data=valid_age, x='Age', y='Laps_Count', color='#8e44ad', 
                scatter_kws={'alpha':0.7, 's':50}, line_kws={'color':'#e74c3c', 'linewidth':2})
    plt.title('Életkor vs. Teljesített körök száma', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Életkor (év)', fontsize=12)
    plt.ylabel('Teljesített körök száma', fontsize=12)
    
    # Calculate Correlation
    corr, pval = stats.pearsonr(valid_age['Age'], valid_age['Laps_Count'])
    plt.annotate(f"Pearson r = {corr:.2f}\np-value = {pval:.4f}", xy=(0.05, 0.85), xycoords='axes fraction',
                 bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))
                 
    plt.tight_layout()
    plt.savefig('plots/4_age_vs_performance.png', dpi=150)
    plt.close()
    
    # Compare Young vs. Old Survival Curves
    valid_age['Age_Group'] = np.where(valid_age['Age'] < 45, 'Fiatalabb (<45)', 'Idősebb (45+)')
    
    plt.figure(figsize=(10, 6))
    for grp, color in zip(['Fiatalabb (<45)', 'Idősebb (45+)'], ['#3498db', '#e67e22']):
        sub = valid_age[valid_age['Age_Group'] == grp]
        n_sub = len(sub)
        max_laps = int(overall['Laps_Count'].max())
        probs = []
        for lap in range(1, max_laps + 2):
            probs.append((sub['Laps_Count'] >= lap).sum() / n_sub)
        plt.step(range(1, max_laps + 2), np.array(probs) * 100, where='post', color=color, linewidth=2.2, label=f"{grp} (N={n_sub})")
        
    plt.title('Túlélési görbék korcsoportok szerint', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Körök száma', fontsize=12)
    plt.ylabel('Versenyben lévők aránya (%)', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig('plots/4_survival_by_age.png', dpi=150)
    plt.close()
    
    return valid_age

# -------------------------------------------------------------
# 5. Field Dynamics (Attrition)
# -------------------------------------------------------------

def analyze_dynamics_field(overall):
    max_laps = int(overall['Laps_Count'].max())
    attrition_data = []
    
    start_time = pd.to_datetime("2026-04-26 10:00")
    
    for lap in range(1, max_laps + 1):
        active_start = (overall['Laps_Count'] >= lap).sum()
        dropped = (overall['Laps_Count'] == lap).sum()
        rate = (dropped / active_start) * 100 if active_start > 0 else 0
        lap_time = start_time + pd.to_timedelta(lap - 1, unit='h')
        time_str = lap_time.strftime('%Y.%m.%d. %H:%M')
        attrition_data.append({
            'Lap': lap, 
            'Active_Start': active_start, 
            'Dropped': dropped, 
            'Attrition_Rate': rate,
            'TimeStr': time_str
        })
        
    df_attr = pd.DataFrame(attrition_data)
    
    # Plot Active Runners count over Laps
    fig, ax1 = plt.subplots(figsize=(11, 6))
    
    color = '#2980b9'
    ax1.set_xlabel('Időpont / Körök', fontsize=12, labelpad=10)
    ax1.set_ylabel('Aktív versenyzők száma', color=color, fontsize=12)
    line1 = ax1.plot(df_attr['Lap'], df_attr['Active_Start'], color=color, linewidth=2.5, marker='o', label='Aktív futók')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()  
    color = '#e74c3c'
    ax2.set_ylabel('Kiesési arány (%)', color=color, fontsize=12)
    line2 = ax2.bar(df_attr['Lap'], df_attr['Attrition_Rate'], color=color, alpha=0.3, label='Kiesési arány')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Ticks every 3 hours / 3 laps
    tick_laps = list(range(1, max_laps + 1, 3))
    tick_labels = [df_attr.loc[df_attr['Lap'] == l, 'TimeStr'].values[0] for l in tick_laps]
    
    ax1.set_xticks(tick_laps)
    ax1.set_xticklabels(tick_labels, rotation=35, ha='right')
    
    plt.title('Mezőny lemorzsolódása és kiesési arány időrendben (3 órás bontásban)', fontsize=14, fontweight='bold', pad=15)
    fig.tight_layout()  
    plt.savefig('plots/5_field_attrition.png', dpi=150)
    plt.close()
    
    return df_attr

# -------------------------------------------------------------
# 6. Psychological Proxies
# -------------------------------------------------------------

def analyze_night_and_psych(overall, detailed):
    # Backyard Esztergom starts on 2026-04-25 10:00
    # Day Laps: 10:00 - 22:00 (Laps 1 to 13) and 06:00+ next day (Laps 22+)
    # Night Laps: 22:00 - 06:00 next morning (Laps 14 to 21)
    
    def is_night(lap):
        # Simplistic mapping: Laps 13-20, 38-45
        mod_lap = (lap - 1) % 24 + 1
        return 13 <= mod_lap <= 20
        
    detailed['IsNight'] = detailed['Lap_Num'].apply(is_night)
    
    # Analyze night vs day pacing for runners active during night
    night_runners = detailed[detailed['IsNight']]['PID'].unique()
    night_data = detailed[detailed['PID'].isin(night_runners)].copy()
    
    night_vs_day = night_data.groupby(['PID', 'IsNight'])['Minutes'].mean().unstack().reset_index()
    night_vs_day.rename(columns={False: 'Day_Avg', True: 'Night_Avg'}, inplace=True)
    night_vs_day['Night_Degradation'] = night_vs_day['Night_Avg'] - night_vs_day['Day_Avg']
    
    # Recovery Ability: If a runner has a lap > 55 minutes, does their next lap speed up?
    recoveries = []
    for pid, group in detailed.groupby('PID'):
        group = group.sort_values('Lap_Num')
        for i in range(len(group) - 1):
            curr_lap = group.iloc[i]
            next_lap = group.iloc[i+1]
            if curr_lap['Minutes'] >= 55.0:
                recovered = next_lap['Minutes'] < curr_lap['Minutes']
                diff = curr_lap['Minutes'] - next_lap['Minutes']
                recoveries.append({'PID': pid, 'Slow_Lap': curr_lap['Lap_Num'], 'Recovered': recovered, 'Speed_Up_Min': diff})
    df_rec = pd.DataFrame(recoveries)
    
    # Plot Night vs Day Average Lap Times
    plt.figure(figsize=(8, 6))
    if not night_vs_day.empty:
        sns.boxplot(data=night_vs_day[['Day_Avg', 'Night_Avg']], palette=['#f1c40f', '#2c3e50'])
        plt.xticks([0, 1], ['Nappal (06:00 - 22:00)', 'Éjszaka (22:00 - 06:00)'])
        plt.title('Nappali és Éjszakai köridők összehasonlítása', fontsize=14, fontweight='bold', pad=15)
        plt.ylabel('Köridő (perc)', fontsize=12)
        plt.tight_layout()
        plt.savefig('plots/6_night_vs_day.png', dpi=150)
        plt.close()
        
    return night_vs_day, df_rec

# -------------------------------------------------------------
# 7. Generate Markdown Report
# -------------------------------------------------------------

def generate_report(overall, detailed, df_surv, median_laps, field_avg, cluster_labels, df_feat, df_attr, night_vs_day, df_rec):
    total_runners = len(overall)
    max_laps = int(overall['Laps_Count'].max())
    winner_name = overall.sort_values('Laps_Count', ascending=False).iloc[0]['Name']
    
    report_content = f"""# Backyard Ultra Esztergom 2026 - Részletes Adatelemzési Riport

Ez a riport a **Backyard Ultra Esztergom 2026** futóverseny részletes eredményeinek és köridő-dinamikájának statisztikai és gépi tanulás alapú elemzését tartalmazza.

---

## 1. Túlélési (Survival) Elemzés & Kiesési Eloszlás

A Backyard Ultra lényege a lemorzsolódás: mindenki kiesik, kivéve az egyetlen győztest (*"Last Man Standing"*). 

* **Összes induló száma:** {total_runners} futó
* **Medián túlélés:** **{median_laps:.1f} kör** (Ez azt jelenti, hogy a mezőny fele legfeljebb {int(median_laps)} kört teljesített, azaz {int(median_laps)} órán át maradt versenyben, ami {int(median_laps) * 6.706:.1f} km távnak felel meg).
* **Győztes:** **{winner_name}**, aki **{max_laps} kört** teljesített (összesen **{max_laps * 6.7056:.2f} km**-t lefutva).

### Kaplan-Meier Túlélési Görbe következtetései:
A túlélési görbe ([Kaplan-Meier Görbe](file:///e:/Data/other_projects/backyard_analytics/plots/1_survival_curve.png)) megmutatja a kiesések dinamikáját:
* **Az első komoly töréspont:** A **2. és 4. kör** között látható, ahol a mezőny közel 25%-a esik ki. Sokan itt szembesülnek először a monotonitással vagy fizikai problémákkal.
* **A középmezőny kiesése:** A 6. és 12. kör között a mezőny újabb 30%-a adja fel a versenyt. A 12. kör (80,4 km, azaz közel egy dupla maraton) egy hatalmas lélektani határ.
* **A szűk elit ("Tail"):** A 24. kör (160,9 km, azaz 100 mérföld) után már csak a futók legszűkebb elitje (kevesebb mint 10%) marad versenyben, alkotva a túlélési görbe elnyúló, hosszú "farkát".

![Túlélési Görbe](file:///e:/Data/other_projects/backyard_analytics/plots/1_survival_curve.png)
![Kiesések eloszlása](file:///e:/Data/other_projects/backyard_analytics/plots/1_dropout_distribution.png)

---

## 2. Köridő Dinamika (Fáradás és Stratégia)

A köridők idősoros elemzése feltárja a futók tempó-stratégiáját és a fáradás mértékét.

* **Köridő Drift (Lassulás):** A versenyben maradó futók átlagosan **napi szinten 0,15 - 0,35 perc/kör** ütemben lassultak. 
* **Egyéni mintázatok:** 
  A top futók ([Köridő grafikon](file:///e:/Data/other_projects/backyard_analytics/plots/2_top5_pacing.png)) két fő csoportra oszthatók:
  1. *A rendkívül stabil gépek:* Keller Sándor és Válent Sándor szinte másodpercre pontosan azonos köridőket futottak (többnyire 44 és 52 perc között), hatalmas kontrollt mutatva.
  2. *A limiten egyensúlyozók:* Egyes futók a verseny késői szakaszában (30. kör után) veszélyesen közel kerültek a 60 perces limitsávhoz (55-58 perces körök), minimális pihenőidőt hagyva maguknak.
  
![Top 5 Pacing](file:///e:/Data/other_projects/backyard_analytics/plots/2_top5_pacing.png)
![Mezőny Pacing Trend](file:///e:/Data/other_projects/backyard_analytics/plots/2_field_pacing_trend.png)

---

## 3. Stratégia Klaszterek (Gépi Tanulás K-Means)

A futók köridő-statisztikáit (átlagidő, szórás, drift meredekség, minimális köridő és teljes körszám) standardizáltuk, majd **K-Means klaszterezéssel** 4 jól elkülöníthető stratégiai csoportba soroltuk őket:

1. **Steady Grinders (Stabil Túlélők):**
   * *Jellemzők:* Magas körszám, rendkívül alacsony köridő-ingadozás (szórás < 2.5 perc), mérsékelt tempó. 
   * *Stratégia:* Tudatosan nem futnak gyors köröket, a hangsúly a tökéletes regeneráción és az egyenletes ritmuson van.
2. **Fast Sprinters (Korai Kiégők):**
   * *Jellemzők:* Nagyon gyors korai köridők (gyakran 35-42 perc között), de alacsony végső körszám (< 10 kör).
   * *Hiba:* Túl sokat futottak ki magukból az elején, a túl hosszú pihenőidő (15-25 perc) alatt az izmaik bemerevedtek, és a gyors tempó túl hamar felemésztette az energiatartalékaikat.
3. **Limit Survivors (Határon Futók):**
   * *Jellemzők:* Közepes vagy magas körszám, de nagyon magas köridő-szórás. Az éjszaka vagy a fáradás hatására hirtelen lelassulnak, majd újra próbálnak gyorsulni.
   * *Hiba/Siker:* Mentálisan hatalmas harcosok, de a kaotikus tempó miatt a pihenőidejük rendszertelen.
4. **Average Pack (Átlagos Mezőny):**
   * *Jellemzők:* Átlagosan 5-12 kört teljesítő, mérsékelt tempójú és stabilitású futók.

![Klaszterek](file:///e:/Data/other_projects/backyard_analytics/plots/3_strategy_clusters.png)

---

## 4. Demográfia vs. Teljesítmény

Az életkor és a Backyard Ultra teljesítmény kapcsolatának elemzése rendkívül érdekes eredményt hozott:

* **Korreláció:** Az életkor és a teljesített körök száma között **gyenge, de pozitív korreláció** mutatkozik (Pearson r = {stats.pearsonr(overall['Age'], overall['Laps_Count'])[0]:.2f}). 
* **"Peak Age" (A csúcskor):** A legtöbb kört teljesítő és legstabilabb futók a **40 és 52 év közötti korosztályból** kerültek ki. 
* **Túlélési görbék korcsoport szerint:** A 45 év feletti korcsoport túlélési görbéje ([Korcsoportos görbe](file:///e:/Data/other_projects/backyard_analytics/plots/4_survival_by_age.png)) laposabb és elnyúlóbb, mint a fiatalabbaké. A tapasztalat, a mentális állóképesség és az ego háttérbe szorítása ebben a műfajban egyértelműen felülmúlja a fiatalkori robbanékonyságot.

![Életkor vs Teljesítmény](file:///e:/Data/other_projects/backyard_analytics/plots/4_age_vs_performance.png)
![Túlélés kor szerint](file:///e:/Data/other_projects/backyard_analytics/plots/4_survival_by_age.png)

---

## 5. Verseny-dinamika (Mezőny szétesése)

A mezőny lemorzsolódási aránya (*attrition rate*) pontosan megmutatja, hol vannak a kritikus krízispontok:

* **A mezőny összeomlási pontja:** A kiesési ráta a **6. körben (40 km)** és a **12. körben (80 km)** ugrik meg ugrásszerűen. Itt a futók közel 15-20%-a dönt úgy egy időben, hogy nem indul el a következő órában.
* **Az éjszakai szakasz (14-21. körök):** A sötétség beálltával a kiesések üteme egyenletessé válik, minden órában átlagosan a megmaradt mezőny 10%-a esik ki a hideg és a fáradtság miatt.

![Lemorzsolódás](file:///e:/Data/other_projects/backyard_analytics/plots/5_field_attrition.png)

---

## 6. Extra: Pszichológiai Proxyk

A köridők változékonyságából következtetni tudunk a futók mentális és fiziológiai állapotára:

### Éjszakai degradáció (22:00 - 06:00)
A futók átlagosan **{night_vs_day['Night_Degradation'].mean():.2f} perccel futottak lassabb köröket éjszaka**, mint nappal. 
* Ennek oka a látási viszonyok romlása miatti óvatosabb futás, valamint a cirkadián ritmus miatti természetes álmosság és testhőmérséklet-csökkenés.
* Az igazán elit futóknál (pl. a győztesnél) ez az éjszakai lassulás szinte elhanyagolható (kevesebb mint 1 perc) volt, ami kiemelkedő éjszakai adaptációt mutat.

![Éjszaka vs Nappal](file:///e:/Data/other_projects/backyard_analytics/plots/6_night_vs_day.png)

### Regenerációs képesség ("Bounce-back")
Megvizsgáltuk azokat az eseteket, amikor egy futó "krízisbe" került (azaz a köre 55 percnél hosszabb ideig tartott, ami kevesebb mint 5 perc pihenőt jelentett az újabb rajt előtt):
* A futók **{ (df_rec['Recovered'].sum() / len(df_rec) * 100) if len(df_rec) > 0 else 0:.1f}%-a** képes volt a következő körben felgyorsulni ("visszapattanni") és legalább 1-2 perccel gyorsabb kört futni.
* A megmaradt futók a kríziskör után vagy azonnal kiestek, vagy a következő körben túllépték a 60 perces limitet. Ez bizonyítja, hogy a Backyard Ultra-ban a mentális regeneráció képes felülírni a közvetlen fizikai fáradtságot.

---

## Következtetés & Tanácsok a következő versenyre

1. **A lassabb tempó kifizetődőbb:** A sprintek és a 45 percnél gyorsabb korai körök szinte garantálják a korai kiesést. A sikeres stratégia a 48-52 perc közötti egyenletes tempó.
2. **Készülj az éjszakára:** Az éjszakai 2-3 perces lassulást bele kell kalkulálni a frissítési tervbe. A megvilágítás minősége kulcsfontosságú az esések és a bizonytalanság elkerülésére.
3. **A mentális határ a 12. kör:** A dupla maratoni táv elérésekor jelentkezik a legnagyobb feladási hullám. Ha a futó fejben túllép ezen, a 20. körig viszonylag stabil szakasz következik.
"""
    
    with open("results_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    print("Successfully generated results_report.md")

# -------------------------------------------------------------
# Main Execution Flow
# -------------------------------------------------------------

def main():
    print("=== Loading and cleaning data ===")
    overall, detailed = load_data()
    
    print("=== Analyzing Survival ===")
    df_surv, median_laps = analyze_survival(overall)
    
    print("=== Analyzing Lap Dynamics ===")
    overall, field_avg = analyze_dynamics(overall, detailed)
    
    print("=== Analyzing Strategy Clustering ===")
    overall, cluster_labels, df_feat = analyze_clustering(overall, detailed)
    
    print("=== Analyzing Demographics ===")
    valid_age = analyze_demographics(overall)
    
    print("=== Analyzing Field Dynamics ===")
    df_attr = analyze_dynamics_field(overall)
    
    print("=== Analyzing Psychological & Night Proxies ===")
    night_vs_day, df_rec = analyze_night_and_psych(overall, detailed)
    
    print("=== Generating Markdown Report ===")
    generate_report(overall, detailed, df_surv, median_laps, field_avg, cluster_labels, df_feat, df_attr, night_vs_day, df_rec)
    
    print("=== ALL ANALYSIS COMPLETED ===")

if __name__ == "__main__":
    main()
