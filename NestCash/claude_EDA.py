import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Matplotlib magyar karakterek támogatása
plt.rcParams['font.family'] = ['DejaVu Sans']
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class FinancialEDA:
    def __init__(self, df):
        """
        Pénzügyi EDA osztály inicializálása
        
        Parameters:
        df (pd.DataFrame): Tranzakciós adatok
        """
        self.df = df.copy()
        self.prepare_data()
        
    def prepare_data(self):
        """Adatok előkészítése az elemzéshez"""
        # Dátum konverzió
        self.df['datum'] = pd.to_datetime(self.df['datum'])
        
        # Összeg numerikus konverzió
        self.df['osszeg'] = pd.to_numeric(self.df['osszeg'], errors='coerce')
        
        # Bevétel/kiadás szétválasztása
        self.df['is_income'] = self.df['osszeg'] > 0
        self.df['abs_osszeg'] = abs(self.df['osszeg'])
        
        # Időbélyegek hozzáadása
        self.df['ev'] = self.df['datum'].dt.year
        self.df['honap_num'] = self.df['datum'].dt.month
        self.df['het_num'] = self.df['datum'].dt.isocalendar().week
        self.df['nap_hete'] = self.df['datum'].dt.dayofweek
        self.df['nap_hete_nev'] = self.df['datum'].dt.day_name()
        
        print(f"Adatok betöltve: {len(self.df)} tranzakció")
        print(f"Időszak: {self.df['datum'].min()} - {self.df['datum'].max()}")
        print(f"Felhasználók száma: {self.df['user_id'].nunique()}")
        
    def basic_statistics(self):
        """Alapvető statisztikák"""
        print("\n" + "="*60)
        print("ALAPVETŐ STATISZTIKÁK")
        print("="*60)
        
        # Összesítő statisztikák
        total_transactions = len(self.df)
        total_income = self.df[self.df['is_income']]['osszeg'].sum()
        total_expense = abs(self.df[~self.df['is_income']]['osszeg'].sum())
        net_flow = total_income - total_expense
        
        print(f"Összes tranzakció: {total_transactions:,}")
        print(f"Összes bevétel: {total_income:,.0f} HUF")
        print(f"Összes kiadás: {total_expense:,.0f} HUF")
        print(f"Nettó cashflow: {net_flow:,.0f} HUF")
        
        # Profil szerinti összesítő
        profile_summary = self.df.groupby('profil').agg({
            'user_id': 'nunique',
            'osszeg': ['count', 'mean', 'sum']
        }).round(0)
        
        print(f"\nProfil szerinti összesítő:")
        print(profile_summary)
        
        return {
            'total_transactions': total_transactions,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_flow': net_flow
        }
    
    def time_series_analysis(self):
        """Idősorok elemzése (havi/heti kiadási minták)"""
        print("\n" + "="*60)
        print("IDŐSOR ELEMZÉS")
        print("="*60)
        
        # Havi aggregálás
        monthly_data = self.df.groupby(['honap', 'is_income']).agg({
            'osszeg': ['sum', 'count', 'mean'],
            'user_id': 'nunique'
        }).round(0)
        
        print("Havi összesítő (bevétel/kiadás):")
        print(monthly_data)
        
        # Heti minták
        weekly_expenses = self.df[~self.df['is_income']].groupby('nap_hete_nev')['abs_osszeg'].agg(['sum', 'mean', 'count'])
        weekly_expenses = weekly_expenses.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        
        print(f"\nHeti kiadási minták:")
        print(weekly_expenses)
        
        # Vizualizáció
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Havi cashflow
        monthly_cashflow = self.df.groupby('honap')['osszeg'].sum()
        monthly_cashflow.plot(kind='bar', ax=axes[0,0], color='skyblue')
        axes[0,0].set_title('Havi Nettó Cashflow')
        axes[0,0].set_ylabel('HUF')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Havi kiadások kategóriánként
        monthly_expenses = self.df[~self.df['is_income']].groupby(['honap', 'kategoria'])['abs_osszeg'].sum().unstack(fill_value=0)
        monthly_expenses.plot(kind='bar', stacked=True, ax=axes[0,1])
        axes[0,1].set_title('Havi Kiadások Kategóriánként')
        axes[0,1].set_ylabel('HUF')
        axes[0,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 3. Heti kiadási minták
        weekly_expenses['sum'].plot(kind='bar', ax=axes[1,0], color='lightcoral')
        axes[1,0].set_title('Heti Kiadási Összegek')
        axes[1,0].set_ylabel('HUF')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Napi tranzakciószám
        daily_count = self.df.groupby('nap_hete_nev').size().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        daily_count.plot(kind='bar', ax=axes[1,1], color='lightgreen')
        axes[1,1].set_title('Napi Tranzakciószám')
        axes[1,1].set_ylabel('Tranzakciók száma')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
        
        return monthly_data, weekly_expenses
    
    def category_analysis(self):
        """Kategóriák szerinti költéselemzés"""
        print("\n" + "="*60)
        print("KATEGÓRIA ELEMZÉS")
        print("="*60)
        
        # Csak kiadások elemzése
        expenses = self.df[~self.df['is_income']].copy()
        
        # Kategória szerinti összesítő
        category_stats = expenses.groupby('kategoria').agg({
            'abs_osszeg': ['sum', 'mean', 'count', 'std'],
            'user_id': 'nunique'
        }).round(0)
        
        category_stats.columns = ['Összes_kiadás', 'Átlag_tranzakció', 'Tranzakciók_száma', 'Szórás', 'Felhasználók_száma']
        category_stats = category_stats.sort_values('Összes_kiadás', ascending=False)
        
        print("Kategóriák szerinti költéselemzés:")
        print(category_stats)
        
        # Top kategóriák
        top_categories = category_stats.head(10)
        
        # Pareto elemzés
        category_stats['Kumulált_százalék'] = (category_stats['Összes_kiadás'].cumsum() / 
                                              category_stats['Összes_kiadás'].sum() * 100).round(1)
        
        print(f"\nPareto elemzés (kumulált százalék):")
        print(category_stats[['Összes_kiadás', 'Kumulált_százalék']].head(10))
        
        # Vizualizáció
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Top 10 kategória pie chart
        top_10 = category_stats.head(10)['Összes_kiadás']
        axes[0,0].pie(top_10.values, labels=top_10.index, autopct='%1.1f%%')
        axes[0,0].set_title('Top 10 Költségkategória (részarány)')
        
        # 2. Kategóriák átlagos tranzakcióértéke
        avg_transaction = category_stats.head(10)['Átlag_tranzakció']
        avg_transaction.plot(kind='barh', ax=axes[0,1], color='orange')
        axes[0,1].set_title('Átlagos Tranzakcióérték Kategóriánként')
        axes[0,1].set_xlabel('HUF')
        
        # 3. Pareto chart
        ax_pareto = axes[1,0]
        bars = ax_pareto.bar(range(len(top_10)), top_10.values, color='skyblue')
        ax_pareto.set_xticks(range(len(top_10)))
        ax_pareto.set_xticklabels(top_10.index, rotation=45, ha='right')
        ax_pareto.set_ylabel('Kiadás (HUF)', color='blue')
        ax_pareto.set_title('Pareto Elemzés - Top 10 Kategória')
        
        # Kumulált százalék vonal
        ax2 = ax_pareto.twinx()
        cumsum_pct = (top_10.cumsum() / category_stats['Összes_kiadás'].sum() * 100)
        ax2.plot(range(len(top_10)), cumsum_pct.values, color='red', marker='o', linewidth=2)
        ax2.set_ylabel('Kumulált %', color='red')
        ax2.set_ylim(0, 100)
        
        # 4. Kategória gyakorisága
        category_freq = expenses['kategoria'].value_counts().head(10)
        category_freq.plot(kind='bar', ax=axes[1,1], color='lightgreen')
        axes[1,1].set_title('Leggyakoribb Kategóriák (tranzakciószám)')
        axes[1,1].set_ylabel('Tranzakciók száma')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
        
        return category_stats
    
    def profile_based_analysis(self):
        """Profil-alapú (jövedelmi szint) költési szokások"""
        print("\n" + "="*60)
        print("PROFIL-ALAPÚ ELEMZÉS")
        print("="*60)
        
        # Profil szerinti összesítő
        profile_analysis = self.df.groupby(['profil', 'is_income']).agg({
            'osszeg': ['sum', 'mean', 'count'],
            'user_id': 'nunique'
        }).round(0)
        
        print("Profil szerinti bevétel/kiadás összesítő:")
        print(profile_analysis)
        
        # Profil szerinti kategória preferenciák
        expenses_by_profile = self.df[~self.df['is_income']].groupby(['profil', 'kategoria'])['abs_osszeg'].sum().unstack(fill_value=0)
        
        # Százalékos megoszlás profil alapján
        profile_category_pct = expenses_by_profile.div(expenses_by_profile.sum(axis=1), axis=0) * 100
        
        print(f"\nKategória preferenciák profilonként (%):")
        print(profile_category_pct.round(1))
        
        # Átlagos tranzakcióérték profil és kategória szerint
        avg_by_profile_cat = self.df[~self.df['is_income']].groupby(['profil', 'kategoria'])['abs_osszeg'].mean().unstack(fill_value=0)
        
        print(f"\nÁtlagos tranzakcióérték profil és kategória szerint:")
        print(avg_by_profile_cat.round(0))
        
        # Vizualizáció
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Profil szerinti összkiadás
        profile_expenses = self.df[~self.df['is_income']].groupby('profil')['abs_osszeg'].sum()
        profile_expenses.plot(kind='bar', ax=axes[0,0], color='coral')
        axes[0,0].set_title('Összkiadás Profilonként')
        axes[0,0].set_ylabel('HUF')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Heatmap - kategória preferenciák
        sns.heatmap(profile_category_pct, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0,1])
        axes[0,1].set_title('Kategória Preferenciák Profilonként (%)')
        
        # 3. Átlagos tranzakcióérték profilonként
        avg_transaction_by_profile = self.df[~self.df['is_income']].groupby('profil')['abs_osszeg'].mean()
        avg_transaction_by_profile.plot(kind='bar', ax=axes[1,0], color='lightblue')
        axes[1,0].set_title('Átlagos Tranzakcióérték Profilonként')
        axes[1,0].set_ylabel('HUF')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Box plot - kiadások szóródása profilonként
        self.df[~self.df['is_income']].boxplot(column='abs_osszeg', by='profil', ax=axes[1,1])
        axes[1,1].set_title('Kiadások Szóródása Profilonként')
        axes[1,1].set_ylabel('HUF (log skála)')
        axes[1,1].set_yscale('log')
        
        plt.tight_layout()
        plt.show()
        
        return profile_analysis, profile_category_pct
    
    def seasonality_analysis(self):
        """Szezonalitás vizsgálata"""
        print("\n" + "="*60)
        print("SZEZONALITÁS ELEMZÉS")
        print("="*60)
        
        # Hónap szerinti elemzés
        monthly_patterns = self.df.groupby(['honap_num', 'kategoria'])['abs_osszeg'].sum().unstack(fill_value=0)
        
        # Hét napjai szerinti mintázatok
        weekday_patterns = self.df.groupby(['nap_hete', 'kategoria'])['abs_osszeg'].sum().unstack(fill_value=0)
        
        # Típus szerinti szezonalitás (alap, impulzus, vagy)
        type_seasonality = self.df.groupby(['honap_num', 'tipus'])['abs_osszeg'].sum().unstack(fill_value=0)
        
        print("Havi költési minták kategóriánként (összeg):")
        print(monthly_patterns.round(0))
        
        print(f"\nTípus szerinti szezonalitás:")
        print(type_seasonality.round(0))
        
        # Vizualizáció
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Havi költési trendek
        monthly_total = self.df[~self.df['is_income']].groupby('honap_num')['abs_osszeg'].sum()
        monthly_total.plot(kind='line', marker='o', ax=axes[0,0], linewidth=2)
        axes[0,0].set_title('Havi Költési Trendek')
        axes[0,0].set_xlabel('Hónap')
        axes[0,0].set_ylabel('HUF')
        axes[0,0].grid(True)
        
        # 2. Heatmap - havi kategória minták
        top_categories = monthly_patterns.sum().nlargest(8).index
        sns.heatmap(monthly_patterns[top_categories].T, annot=True, fmt='.0f', cmap='Blues', ax=axes[0,1])
        axes[0,1].set_title('Havi Kategória Minták (Top 8)')
        axes[0,1].set_xlabel('Hónap')
        
        # 3. Hét napjai szerinti minták
        weekday_total = self.df[~self.df['is_income']].groupby('nap_hete')['abs_osszeg'].sum()
        weekday_names = ['Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat', 'Vasárnap']
        weekday_total.index = weekday_names
        weekday_total.plot(kind='bar', ax=axes[1,0], color='orange')
        axes[1,0].set_title('Heti Költési Minták')
        axes[1,0].set_ylabel('HUF')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 4. Impulzus vs tervezett vásárlások
        impulse_vs_planned = self.df[~self.df['is_income']].groupby('tipus')['abs_osszeg'].sum()
        impulse_vs_planned.plot(kind='pie', ax=axes[1,1], autopct='%1.1f%%')
        axes[1,1].set_title('Impulzus vs Tervezett Vásárlások')
        
        plt.tight_layout()
        plt.show()
        
        return monthly_patterns, weekday_patterns, type_seasonality
    
    def income_expense_ratio(self):
        """Income-expense ratio profilonként"""
        print("\n" + "="*60)
        print("INCOME-EXPENSE RATIO ELEMZÉS")
        print("="*60)
        
        # User szintű aggregálás - javított verzió
        user_summary = self.df.groupby(['user_id', 'profil']).agg({
            'osszeg': lambda x: x[x > 0].sum(),  # Bevételek
            'abs_osszeg': lambda x: x[self.df.loc[x.index, 'osszeg'] < 0].sum()  # Kiadások
        }).rename(columns={'osszeg': 'bevetel', 'abs_osszeg': 'kiadas'})
        
        # Index reset hogy profil oszlop legyen
        user_summary = user_summary.reset_index()
        
        # Ratio számítás - védekezés nullával való osztás ellen
        user_summary['savings_rate'] = np.where(
            user_summary['bevetel'] > 0,
            ((user_summary['bevetel'] - user_summary['kiadas']) / user_summary['bevetel'] * 100).round(1),
            -100  # Ha nincs bevétel, akkor -100% savings rate
        )
        user_summary['expense_ratio'] = np.where(
            user_summary['bevetel'] > 0,
            (user_summary['kiadas'] / user_summary['bevetel'] * 100).round(1),
            0  # Ha nincs bevétel, expense ratio 0
        )
        
        # Profil szintű összesítő
        profile_ratios = user_summary.groupby('profil').agg({
            'bevetel': ['mean', 'median'],
            'kiadas': ['mean', 'median'],
            'savings_rate': ['mean', 'median', 'std'],
            'expense_ratio': ['mean', 'median', 'std']
        }).round(1)
        
        print("Profil szerinti income-expense ratios:")
        print(profile_ratios)
        
        # Részletes user szintű statisztikák
        print(f"\nUser szintű savings rate statisztikák:")
        print(user_summary.groupby('profil')['savings_rate'].describe().round(1))
        
        # Kockázati kategorizálás
        user_summary['risk_category'] = pd.cut(user_summary['savings_rate'], 
                                             bins=[-np.inf, 0, 10, 20, np.inf],
                                             labels=['Magas kockázat', 'Közepes kockázat', 'Alacsony kockázat', 'Kiváló'])
        
        risk_distribution = user_summary.groupby(['profil', 'risk_category']).size().unstack(fill_value=0)
        print(f"\nKockázati kategóriák eloszlása profilonként:")
        print(risk_distribution)
        
        # Vizualizáció
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Savings rate eloszlás profilonként
        user_summary.boxplot(column='savings_rate', by='profil', ax=axes[0,0])
        axes[0,0].set_title('Megtakarítási Ráta Eloszlása Profilonként')
        axes[0,0].set_ylabel('Megtakarítási ráta (%)')
        
        # 2. Expense ratio összehasonlítás
        profile_expense_ratios = user_summary.groupby('profil')['expense_ratio'].mean()
        profile_expense_ratios.plot(kind='bar', ax=axes[0,1], color='lightcoral')
        axes[0,1].set_title('Átlagos Kiadási Arány Profilonként')
        axes[0,1].set_ylabel('Kiadási arány (%)')
        axes[0,1].tick_params(axis='x', rotation=45)
        axes[0,1].axhline(y=100, color='red', linestyle='--', alpha=0.7, label='100% küszöb')
        axes[0,1].legend()
        
        # 3. Scatter plot - bevétel vs megtakarítás
        colors = {'alacsony_jov': 'red', 'kozeposztaly': 'blue', 'magas_jov': 'green', 'arerzekeny': 'orange'}
        for profile in user_summary['profil'].unique():
            subset = user_summary[user_summary['profil'] == profile]
            axes[1,0].scatter(subset['bevetel'], subset['savings_rate'], 
                            label=profile, color=colors.get(profile, 'gray'), alpha=0.7)
        axes[1,0].set_xlabel('Havi bevétel (HUF)')
        axes[1,0].set_ylabel('Megtakarítási ráta (%)')
        axes[1,0].set_title('Bevétel vs Megtakarítási Ráta')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Kockázati kategóriák
        risk_pct = risk_distribution.div(risk_distribution.sum(axis=1), axis=0) * 100
        risk_pct.plot(kind='bar', stacked=True, ax=axes[1,1])
        axes[1,1].set_title('Kockázati Kategóriák Eloszlása (%)')
        axes[1,1].set_ylabel('Százalék')
        axes[1,1].tick_params(axis='x', rotation=45)
        axes[1,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.show()
        
        return user_summary, profile_ratios, risk_distribution
    
    def generate_insights(self):
        """Automatikus insights generálása"""
        print("\n" + "="*60)
        print("AUTOMATIKUS INSIGHTS")
        print("="*60)
        
        insights = []
        
        # 1. Top költségkategória
        top_category = self.df[~self.df['is_income']].groupby('kategoria')['abs_osszeg'].sum().idxmax()
        top_amount = self.df[~self.df['is_income']].groupby('kategoria')['abs_osszeg'].sum().max()
        insights.append(f"• Legnagyobb költségkategória: {top_category} ({top_amount:,.0f} HUF)")
        
        # 2. Legaktívabb nap
        most_active_day = self.df['nap_hete_nev'].value_counts().idxmax()
        insights.append(f"• Legaktívabb nap: {most_active_day}")
        
        # 3. Impulzus vásárlások aránya
        impulse_pct = (self.df[self.df['tipus'] == 'impulzus']['abs_osszeg'].sum() / 
                      self.df[~self.df['is_income']]['abs_osszeg'].sum() * 100)
        insights.append(f"• Impulzus vásárlások aránya: {impulse_pct:.1f}%")
        
        # 4. Legkockázatosabb profil - javított verzió
        user_summary = self.df.groupby(['user_id', 'profil']).agg({
            'osszeg': lambda x: x[x > 0].sum(),
            'abs_osszeg': lambda x: x[self.df.loc[x.index, 'osszeg'] < 0].sum()
        }).rename(columns={'osszeg': 'bevetel', 'abs_osszeg': 'kiadas'})
        
        # Index reset
        user_summary = user_summary.reset_index()
        
        # Savings rate számítás védelem nullával való osztás ellen
        user_summary['savings_rate'] = np.where(
            user_summary['bevetel'] > 0,
            ((user_summary['bevetel'] - user_summary['kiadas']) / user_summary['bevetel'] * 100),
            -100
        )
        
        lowest_savings_profile = user_summary.groupby('profil')['savings_rate'].mean().idxmin()
        insights.append(f"• Legalacsonyabb megtakarítási rátájú profil: {lowest_savings_profile}")
        
        # 5. Fix vs változó költségek
        fixed_pct = (self.df[self.df['fix_koltseg'] == True]['abs_osszeg'].sum() / 
                    self.df[~self.df['is_income']]['abs_osszeg'].sum() * 100)
        insights.append(f"• Fix költségek aránya: {fixed_pct:.1f}%")
        
        print("\n".join(insights))
        
        return insights

# Használat
def run_complete_eda(df):
    """Teljes EDA futtatása"""
    print("🔍 PÉNZÜGYI EDA ELEMZÉS INDÍTÁSA")
    print("="*80)
    
    # EDA objektum létrehozása
    eda = FinancialEDA(df)
    
    # Elemzések futtatása
    basic_stats = eda.basic_statistics()
    time_analysis = eda.time_series_analysis()
    category_analysis = eda.category_analysis()
    profile_analysis = eda.profile_based_analysis()
    seasonality_analysis = eda.seasonality_analysis()
    ratio_analysis = eda.income_expense_ratio()
    insights = eda.generate_insights()
    
    print(f"\n{'='*80}")
    print("✅ EDA ELEMZÉS BEFEJEZVE")
    print("="*80)
    
    return eda

#%% Példa futtatás
df = pd.read_csv('szintetikus_tranzakciok.csv')
eda_results = run_complete_eda(df)
