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

class UserFinancialEDA:
    def __init__(self, df):
        """
        User-specifikus pénzügyi EDA osztály inicializálása
        
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
        
        print(f"Adatok betöltve: {len(self.df)} tranzakció, {self.df['user_id'].nunique()} felhasználó")
    
    def prepare_user_data(self, user_data):
        """Adatok előkészítése dashboardhoz (külön metódusba kiszervezve)"""
        user_data = user_data.copy()
        
        # Dátum konverzió
        user_data['datum'] = pd.to_datetime(user_data['datum'])
        
        # Összeg numerikus konverzió
        user_data['osszeg'] = pd.to_numeric(user_data['osszeg'], errors='coerce')
        
        # Bevétel/kiadás szétválasztása
        user_data['is_income'] = user_data['osszeg'] > 0
        user_data['abs_osszeg'] = abs(user_data['osszeg'])
        
        # Időbélyegek hozzáadása
        user_data['honap'] = user_data['datum'].dt.strftime('%Y-%m')
        user_data['nap_hete'] = user_data['datum'].dt.dayofweek
        user_data['nap_hete_nev'] = user_data['datum'].dt.day_name()
        
        return user_data
    
    def analyze_user(self, user_id, show_plots=True):
        """
        Egy adott user részletes elemzése benchmarkolással
        
        Parameters:
        user_id: Elemzendő felhasználó ID
        show_plots: Vizualizációk megjelenítése
        """
        print(f"\n{'='*80}")
        print(f"🎯 SZEMÉLYES PÉNZÜGYI JELENTÉS - User ID: {user_id}")
        print(f"{'='*80}")
        
        # User adatok szűrése
        user_data = self.df[self.df['user_id'] == user_id].copy()
        
        if len(user_data) == 0:
            print(f"❌ Nincs adat a {user_id} user-hez!")
            return None
            
        user_profile = user_data['profil'].iloc[0]
        
        # Benchmark adatok (hasonló profil + összes user)
        profile_data = self.df[self.df['profil'] == user_profile].copy()
        all_data = self.df.copy()
        
        print(f"📊 Elemzett időszak: {user_data['datum'].min().strftime('%Y-%m-%d')} - {user_data['datum'].max().strftime('%Y-%m-%d')}")
        print(f"📈 Tranzakciók száma: {len(user_data)}")
        
        # 1. ALAPSTATISZTIKÁK ÉS BENCHMARKING
        self._basic_user_stats(user_data, profile_data, all_data, user_profile)
        
        # 2. CASH FLOW ELEMZÉS
        self._cashflow_analysis(user_data, profile_data, user_profile)
        
        # 3. KÖLTÉSI SZOKÁSOK ELEMZÉSE
        self._spending_patterns(user_data, profile_data, user_profile)
        
        # 4. KATEGÓRIA ELEMZÉS BENCHMARKOLÁSSAL
        self._category_benchmark(user_data, profile_data, user_profile)
        
        # 5. IDŐBELI TRENDEK
        self._temporal_analysis(user_data, user_profile)
        
        # 6. KOCKÁZATI ELEMZÉS
        self._risk_analysis(user_data, profile_data, user_profile)
        
        # 7. SZEMÉLYRE SZABOTT JAVASLATOK
        recommendations = self._generate_recommendations(user_data, profile_data, user_profile)
            
        # Fő report dictionary
        report = {}
        
        # 1. Alapstatisztikák
        report['basic_stats'] = self._basic_user_stats(user_data, profile_data, all_data, user_profile)
        
        # 2. Cashflow elemzés
        report['cashflow'] = self._cashflow_analysis(user_data, profile_data, user_profile)
        
        # 3. Költési szokások
        report['spending_patterns'] = self._spending_patterns(user_data, profile_data, user_profile)
                
        return {
            'user_id': user_id,
            'profile': user_profile,
            'time_period': {
                'start': user_data['datum'].min().strftime('%Y-%m-%d'),
                'end': user_data['datum'].max().strftime('%Y-%m-%d')
            },
            'transaction_count': len(user_data),
            'basic_stats': self._basic_user_stats(user_data, profile_data, all_data, user_profile),
            'cashflow': self._cashflow_analysis(user_data, profile_data, user_profile),
            'spending_patterns': self._spending_patterns(user_data, profile_data, user_profile),
            'category_analysis': self._category_benchmark(user_data, profile_data, user_profile),
            'temporal_analysis': self._temporal_analysis(user_data, user_profile),
            'risk_analysis': self._risk_analysis(user_data, profile_data, user_profile),
            'recommendations': self._generate_recommendations(user_data, profile_data, user_profile),
        }
    
    def _basic_user_stats(self, user_data, profile_data, all_data, user_profile):
        """Alapstatisztikák user vs benchmark"""
        print(f"\n📊 ALAPSTATISZTIKÁK ÉS BENCHMARKING")
        print("-" * 50)
        
        # User statisztikák
        user_income = user_data[user_data['is_income']]['osszeg'].sum()
        user_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
        user_net = user_income - user_expenses
        user_savings_rate = (user_net / user_income * 100) if user_income > 0 else 0
        
        # Benchmark statisztikák (profil átlag)
        profile_users = profile_data.groupby('user_id').agg({
            'osszeg': lambda x: x[x > 0].sum(),  # bevételek
            'abs_osszeg': lambda x: x[profile_data.loc[x.index, 'osszeg'] < 0].sum()  # kiadások
        }).rename(columns={'osszeg': 'bevetel', 'abs_osszeg': 'kiadas'})
        
        profile_users['net'] = profile_users['bevetel'] - profile_users['kiadas']
        profile_users['savings_rate'] = (profile_users['net'] / profile_users['bevetel'] * 100).fillna(0)
        
        benchmark_income = profile_users['bevetel'].mean()
        benchmark_expenses = profile_users['kiadas'].mean()
        benchmark_savings_rate = profile_users['savings_rate'].mean()
        
        print(f"💰 Havi bevétel: {user_income:,.0f} HUF")
        print(f"   📈 Profil átlag: {benchmark_income:,.0f} HUF ({self._compare_to_benchmark(user_income, benchmark_income)})")
        
        print(f"💸 Havi kiadás: {user_expenses:,.0f} HUF")
        print(f"   📈 Profil átlag: {benchmark_expenses:,.0f} HUF ({self._compare_to_benchmark(user_expenses, benchmark_expenses, reverse=True)})")
        
        print(f"💎 Nettó megtakarítás: {user_net:,.0f} HUF")
        print(f"🎯 Megtakarítási ráta: {user_savings_rate:.1f}%")
        print(f"   📈 Profil átlag: {benchmark_savings_rate:.1f}% ({self._compare_to_benchmark(user_savings_rate, benchmark_savings_rate)})")
        
        # Percentilis rangsor
        user_rank_income = (profile_users['bevetel'] < user_income).mean() * 100
        user_rank_savings = (profile_users['savings_rate'] < user_savings_rate).mean() * 100
        
        print(f"\n🏆 RANGSOR A PROFILON BELÜL:")
        print(f"   💰 Bevétel: {user_rank_income:.0f}. percentilis")
        print(f"   💎 Megtakarítási ráta: {user_rank_savings:.0f}. percentilis")
        
        # Adatgyűjtés dictionary létrehozása
        stats = {
            'user_income': user_income,
            'user_expenses': user_expenses,
            'user_net': user_net,
            'user_savings_rate': user_savings_rate,
            'benchmark_income': benchmark_income,
            'benchmark_expenses': benchmark_expenses,
            'benchmark_savings_rate': benchmark_savings_rate,
            'user_rank_income': user_rank_income,
            'user_rank_savings': user_rank_savings
        }
        
        return stats
    
    def _cashflow_analysis(self, user_data, profile_data, user_profile):
        """Cashflow elemzés és trend"""
        print(f"\n💹 CASHFLOW ELEMZÉS")
        print("-" * 30)
        
        # Havi cashflow trend
        monthly_flow = user_data.groupby('honap')['osszeg'].sum()
        
        print(f"📅 HAVI CASHFLOW TREND:")
        for month, flow in monthly_flow.items():
            trend_emoji = "📈" if flow > 0 else "📉" if flow < -50000 else "➡️"
            print(f"   {month}: {flow:,.0f} HUF {trend_emoji}")
        
        # Trend elemzés
        if len(monthly_flow) > 1:
            trend = monthly_flow.pct_change().mean()
            if abs(trend) < 0.1:
                trend_msg = "Stabil cashflow 📊"
            elif trend > 0:
                trend_msg = f"Javuló trend (+{trend*100:.1f}% havi átlag) 📈"
            else:
                trend_msg = f"Romló trend ({trend*100:.1f}% havi átlag) 📉"
            print(f"\n🔍 Trend értékelés: {trend_msg}")
    
        cashflow_data = {
            'monthly_flow': monthly_flow.to_dict(),
            'trend': trend,
            'trend_msg': trend_msg
        }
        
        return cashflow_data
    
    def _spending_patterns(self, user_data, profile_data, user_profile):
        """Költési szokások elemzése"""
        print(f"\n🛒 KÖLTÉSI SZOKÁSOK ELEMZÉSE")
        print("-" * 35)
        
        user_expenses = user_data[~user_data['is_income']]
        
        # Költési típusok
        spending_types = user_expenses.groupby('tipus')['abs_osszeg'].sum()
        total_expenses = spending_types.sum()
        
        print(f"💳 KÖLTÉSI TÍPUSOK:")
        for stype, amount in spending_types.items():
            percentage = (amount / total_expenses * 100)
            emoji = {"alap": "🏠", "impulzus": "⚡", "vagy": "🤔"}.get(stype, "💸")
            print(f"   {emoji} {stype}: {amount:,.0f} HUF ({percentage:.1f}%)")
        
        # Impulzus vásárlási hajlam vs benchmark
        user_impulse_pct = (spending_types.get('impulzus', 0) / total_expenses * 100)
        
        profile_impulse = profile_data[~profile_data['is_income']].groupby('tipus')['abs_osszeg'].sum()
        profile_impulse_pct = (profile_impulse.get('impulzus', 0) / profile_impulse.sum() * 100)
        
        print(f"\n⚡ IMPULZUS VÁSÁRLÁSI HAJLAM:")
        print(f"   Te: {user_impulse_pct:.1f}%")
        print(f"   Profil átlag: {profile_impulse_pct:.1f}%")
        
        if user_impulse_pct > profile_impulse_pct * 1.2:
            print(f"   ⚠️ Átlag feletti impulzus vásárlási hajlam!")
        elif user_impulse_pct < profile_impulse_pct * 0.8:
            print(f"   ✅ Átlag alatti impulzus vásárlási hajlam - jó önkontroll!")
        
        # Fix vs változó költségek
        fixed_costs = user_expenses[user_expenses['fix_koltseg'] == True]['abs_osszeg'].sum()
        variable_costs = user_expenses[user_expenses['fix_koltseg'] == False]['abs_osszeg'].sum()
        
        print(f"\n🏠 FIX VS VÁLTOZÓ KÖLTSÉGEK:")
        print(f"   🔒 Fix költségek: {fixed_costs:,.0f} HUF ({fixed_costs/total_expenses*100:.1f}%)")
        print(f"   🔄 Változó költségek: {variable_costs:,.0f} HUF ({variable_costs/total_expenses*100:.1f}%)")
        
        spending_data = {
            'spending_types': spending_types.to_dict(),
            'total_expenses': float(total_expenses),
            'user_impulse_pct': float(user_impulse_pct),
            'profile_impulse_pct': float(profile_impulse_pct),
            'fixed_costs': float(fixed_costs),
            'variable_costs': float(variable_costs),
            'fixed_ratio': float(fixed_costs / total_expenses * 100) if total_expenses > 0 else 0,
            'variable_ratio': float(variable_costs / total_expenses * 100) if total_expenses > 0 else 0
        }
        return spending_data  # Beszúrás a metódus végére
        
    def _category_benchmark(self, user_data, profile_data, user_profile):
        """Kategória szintű benchmarking"""
        print(f"\n🏷️ KATEGÓRIA BENCHMARKING")
        print("-" * 30)
        
        user_expenses = user_data[~user_data['is_income']]
        profile_expenses = profile_data[~profile_data['is_income']]
        
        # User kategóriák
        user_categories = user_expenses.groupby('kategoria')['abs_osszeg'].sum().sort_values(ascending=False)
        total_user_expenses = user_categories.sum()
        
        # Profil átlag kategóriák (user átlagban)
        profile_users_cat = profile_expenses.groupby(['user_id', 'kategoria'])['abs_osszeg'].sum().reset_index()
        profile_avg_cat = profile_users_cat.groupby('kategoria')['abs_osszeg'].mean()
        
        print(f"🏆 TOP 5 KÖLTSÉGKATEGÓRIA:")
        top_categories = {}
        for i, (category, amount) in enumerate(user_categories.head(5).items(), 1):
            percentage = (amount / total_user_expenses * 100)
            profile_avg = profile_avg_cat.get(category, 0)
            top_categories[i] = {'name': category,
                                 'amount': amount,
                                 'percentage': percentage
                                 }
            
            if profile_avg > 0:
                comparison = self._compare_to_benchmark(amount, profile_avg, reverse=True)
                print(f"   {i}. {category}: {amount:,.0f} HUF ({percentage:.1f}%) - {comparison} (profil átlaghoz képest)")
            else:
                print(f"   {i}. {category}: {amount:,.0f} HUF ({percentage:.1f}%)")
        
        # Hiányzó alapvető kategóriák ellenőrzése
        essential_categories = ['elelmiszer', 'lakber', 'kozlekedes', 'egeszseg']
        missing_essentials = [cat for cat in essential_categories if cat not in user_categories.index]
        
        if missing_essentials:
            print(f"\n⚠️ HIÁNYZÓ ALAPVETŐ KATEGÓRIÁK:")
            for cat in missing_essentials:
                print(f"   ❌ {cat}")

        category_data = {
            'user_categories': user_categories.to_dict(),
            'top_category': top_categories,
            'missing_essentials': missing_essentials,
            'profile_avg_categories': profile_avg_cat.to_dict()
        }
        return category_data  # Beszúrás a metódus végére
        
    def _temporal_analysis(self, user_data, user_profile):
        """Időbeli költési minták"""
        print(f"\n📅 IDŐBELI KÖLTÉSI MINTÁK")
        print("-" * 30)
        
        user_expenses = user_data[~user_data['is_income']]
        
        # Heti minták
        weekly_spending = user_expenses.groupby('nap_hete_nev')['abs_osszeg'].sum()
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_spending = weekly_spending.reindex(weekday_names, fill_value=0)
        
        max_day = weekly_spending.idxmax()
        min_day = weekly_spending.idxmin()
        
        print(f"📊 HETI KÖLTÉSI MINTÁK:")
        print(f"   💸 Legköltekenyebb nap: {max_day} ({weekly_spending[max_day]:,.0f} HUF)")
        print(f"   💰 Legspórolósabb nap: {min_day} ({weekly_spending[min_day]:,.0f} HUF)")
        
        # Hétvége vs hétköznap
        weekend_days = ['Saturday', 'Sunday']
        weekday_avg = weekly_spending[~weekly_spending.index.isin(weekend_days)].mean()
        weekend_avg = weekly_spending[weekly_spending.index.isin(weekend_days)].mean()
        
        print(f"   🏢 Hétköznapi átlag: {weekday_avg:,.0f} HUF")
        print(f"   🏖️ Hétvégi átlag: {weekend_avg:,.0f} HUF")
        
        if weekend_avg > weekday_avg * 1.3:
            print(f"   ⚠️ Jelentősen magasabb hétvégi költések!")
    
        temporal_data = {
            'weekly_spending': weekly_spending.to_dict(),
            'max_day': {
                'name': max_day,
                'amount': float(weekly_spending[max_day])
            },
            'min_day': {
                'name': min_day,
                'amount': float(weekly_spending[min_day])
            },
            'weekday_avg': float(weekday_avg),
            'weekend_avg': float(weekend_avg),
            'weekend_spending_ratio': float(weekend_avg / weekday_avg) if weekday_avg > 0 else 0
        }
        return temporal_data  # Beszúrás a metódus végére
            
    def _risk_analysis(self, user_data, profile_data, user_profile):
        """Pénzügyi kockázati elemzés"""
        print(f"\n⚠️ PÉNZÜGYI KOCKÁZATI ELEMZÉS")
        print("-" * 35)
        
        user_income = user_data[user_data['is_income']]['osszeg'].sum()
        user_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
        
        # Expense ratio
        expense_ratio = (user_expenses / user_income * 100) if user_income > 0 else 0
        
        # Kockázati kategóriák
        if expense_ratio >= 100:
            risk_level = "🔴 MAGAS KOCKÁZAT"
            risk_msg = "Kiadások meghaladják a bevételeket!"
        elif expense_ratio >= 90:
            risk_level = "🟡 KÖZEPES KOCKÁZAT"
            risk_msg = "Nagyon alacsony megtakarítási ráta"
        elif expense_ratio >= 80:
            risk_level = "🟢 ALACSONY KOCKÁZAT"
            risk_msg = "Elfogadható pénzügyi helyzet"
        else:
            risk_level = "🌟 KIVÁLÓ"
            risk_msg = "Egészséges pénzügyi helyzet"
        
        print(f"🎯 Kockázati szint: {risk_level}")
        print(f"📊 Kiadási arány: {expense_ratio:.1f}%")
        print(f"💡 Értékelés: {risk_msg}")
        
        # Fix költségek aránya
        user_expenses_detail = user_data[~user_data['is_income']]
        fixed_costs = user_expenses_detail[user_expenses_detail['fix_koltseg'] == True]['abs_osszeg'].sum()
        fixed_ratio = (fixed_costs / user_income * 100) if user_income > 0 else 0
        
        print(f"\n🔒 Fix költségek aránya: {fixed_ratio:.1f}%")
        if fixed_ratio > 60:
            print(f"   ⚠️ Magas fix költség arány - korlátozott rugalmasság!")
        elif fixed_ratio < 40:
            print(f"   ✅ Alacsony fix költség arány - jó rugalmasság!")
        
        risk_data = {
            'expense_ratio': float(expense_ratio),
            'risk_level': risk_level,
            'risk_msg': risk_msg,
            'fixed_ratio': float(fixed_ratio),
            'income': float(user_income),
            'expenses': float(user_expenses)
        }
        return risk_data  # Beszúrás a metódus végére
        
    def _generate_recommendations(self, user_data, profile_data, user_profile):
        """Személyre szabott javaslatok generálása"""
        print(f"\n💡 SZEMÉLYRE SZABOTT JAVASLATOK")
        print("-" * 40)
        
        recommendations = []
        
        user_income = user_data[user_data['is_income']]['osszeg'].sum()
        user_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
        savings_rate = ((user_income - user_expenses) / user_income * 100) if user_income > 0 else 0
        
        user_expenses_detail = user_data[~user_data['is_income']]
        
        # 1. Megtakarítási ráta alapú javaslatok
        if savings_rate < 0:
            recommendations.append("🚨 AZONNALI CSELEKVÉS: Kiadások csökkentése szükséges!")
            recommendations.append("💡 Vizsgáld felül a nem alapvető kiadásokat")
        elif savings_rate < 10:
            recommendations.append("📈 Cél: 10-20% megtakarítási ráta elérése")
            recommendations.append("💡 Keresi a költségoptimalizálási lehetőségeket")
        elif savings_rate > 30:
            recommendations.append("🌟 Kiváló megtakarítási ráta!")
            recommendations.append("💡 Befektetési lehetőségek mérlegelése")
        
        # 2. Impulzus vásárlások
        impulse_spending = user_expenses_detail[user_expenses_detail['tipus'] == 'impulzus']['abs_osszeg'].sum()
        impulse_pct = (impulse_spending / user_expenses * 100) if user_expenses > 0 else 0
        
        if impulse_pct > 15:
            recommendations.append(f"⚡ Impulzus vásárlások csökkentése ({impulse_pct:.1f}%)")
            recommendations.append("💡 24 órás gondolkodási idő nagy vásárlásoknál")
        
        # 3. Kategória specifikus javaslatok
        categories = user_expenses_detail.groupby('kategoria')['abs_osszeg'].sum()
        top_category = categories.idxmax()
        top_amount = categories.max()
        top_pct = (top_amount / user_expenses * 100)
        
        if top_pct > 40:
            recommendations.append(f"🎯 {top_category} kategória optimalizálása ({top_pct:.1f}%)")
        
        # 4. Fix költségek
        fixed_costs = user_expenses_detail[user_expenses_detail['fix_koltseg'] == True]['abs_osszeg'].sum()
        fixed_ratio = (fixed_costs / user_income * 100) if user_income > 0 else 0
        
        if fixed_ratio > 60:
            recommendations.append("🔒 Fix költségek felülvizsgálata szükséges")
            recommendations.append("💡 Szerződések újratárgyalása, szolgáltatók váltása")
        
        # 5. Időbeli minták
        weekend_spending = user_expenses_detail[user_expenses_detail['nap_hete'].isin([5, 6])]['abs_osszeg'].sum()
        weekday_spending = user_expenses_detail[~user_expenses_detail['nap_hete'].isin([5, 6])]['abs_osszeg'].sum()
        
        if weekend_spending > weekday_spending * 0.5:  # hétvégén több mint a hét felét költi
            recommendations.append("🏖️ Hétvégi költések tudatosabb tervezése")
        
        # Javaslatok kiírása
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        return recommendations
    
    def _create_user_dashboard(self, user_data, profile_data, user_profile):
        """User dashboard létrehozása"""
        # Adatok előkészítése
        user_data = self.prepare_user_data(user_data)
        profile_data = self.prepare_user_data(profile_data)
        
        # Dashboard létrehozása
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'Személyes Pénzügyi Dashboard - {user_profile} profil', 
                    fontsize=16, fontweight='bold')
    
        user_expenses = user_data[~user_data['is_income']]
        
        # 1. Havi cashflow
        monthly_flow = user_data.groupby('honap')['osszeg'].sum()
        colors = ['green' if x > 0 else 'red' for x in monthly_flow.values]
        monthly_flow.plot(kind='bar', ax=axes[0,0], color=colors)
        axes[0,0].set_title('Havi Cashflow')
        axes[0,0].set_ylabel('HUF')
        axes[0,0].axhline(y=0, color='black', linestyle='-', alpha=0.5)
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Kategória megoszlás
        categories = user_expenses.groupby('kategoria')['abs_osszeg'].sum().head(8)
        axes[0,1].pie(categories.values, labels=categories.index, autopct='%1.1f%%')
        axes[0,1].set_title('Költségkategóriák megoszlása')
        
        # 3. Költési típusok
        spending_types = user_expenses.groupby('tipus')['abs_osszeg'].sum()
        spending_types.plot(kind='bar', ax=axes[0,2], color=['skyblue', 'orange', 'lightgreen'])
        axes[0,2].set_title('Költési típusok')
        axes[0,2].set_ylabel('HUF')
        axes[0,2].tick_params(axis='x', rotation=45)
        
        # 4. Heti költési minták
        weekly_spending = user_expenses.groupby('nap_hete_nev')['abs_osszeg'].sum()
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_spending = weekly_spending.reindex(weekday_names, fill_value=0)
        weekly_spending.plot(kind='bar', ax=axes[1,0], color='lightcoral')
        axes[1,0].set_title('Heti költési minták')
        axes[1,0].set_ylabel('HUF')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 5. Benchmarking - megtakarítási ráta
        user_income = user_data[~user_data['is_income']]['osszeg'].sum()
        user_expenses_sum = user_expenses['abs_osszeg'].sum()
        user_savings_rate = ((user_income - user_expenses_sum) / user_income * 100) if user_income > 0 else 0
        
        # Profil benchmark
        profile_users = profile_data.groupby('user_id').agg({
            'osszeg': lambda x: x[x > 0].sum(),
            'abs_osszeg': lambda x: x[profile_data.loc[x.index, 'osszeg'] < 0].sum()
        }).rename(columns={'osszeg': 'bevetel', 'abs_osszeg': 'kiadas'})
        profile_users['savings_rate'] = ((profile_users['bevetel'] - profile_users['kiadas']) / profile_users['bevetel'] * 100).fillna(0)
        
        axes[1,1].hist(profile_users['savings_rate'], bins=15, alpha=0.7, color='lightblue', label=f'{user_profile} profil')
        axes[1,1].axvline(user_savings_rate, color='red', linestyle='--', linewidth=2, label='Te')
        axes[1,1].set_title('Megtakarítási ráta összehasonlítás')
        axes[1,1].set_xlabel('Megtakarítási ráta (%)')
        axes[1,1].set_ylabel('Felhasználók száma')
        axes[1,1].legend()
        
        # 6. Fix vs változó költségek
        fixed_costs = user_expenses[user_expenses['fix_koltseg'] == True]['abs_osszeg'].sum()
        variable_costs = user_expenses[user_expenses['fix_koltseg'] == False]['abs_osszeg'].sum()
        
        cost_types = pd.Series([fixed_costs, variable_costs], index=['Fix költségek', 'Változó költségek'])
        cost_types.plot(kind='pie', ax=axes[1,2], autopct='%1.1f%%', colors=['lightsteelblue', 'lightsalmon'])
        axes[1,2].set_title('Fix vs Változó költségek')
        
        plt.tight_layout()
        return fig
    
    def _compare_to_benchmark(self, user_value, benchmark_value, reverse=False):
        """Benchmark összehasonlítás szöveges kiértékelése"""
        if benchmark_value == 0:
            return "nincs összehasonlítási alap"
        
        ratio = user_value / benchmark_value
        
        if reverse:  # kisebb érték jobb (pl. kiadások)
            if ratio < 0.8:
                return "✅ jelentősen alacsonyabb"
            elif ratio < 0.95:
                return "👍 alacsonyabb"
            elif ratio < 1.05:
                return "➡️ hasonló"
            elif ratio < 1.2:
                return "⚠️ magasabb"
            else:
                return "🔴 jelentősen magasabb"
        else:  # nagyobb érték jobb (pl. bevétel, megtakarítás)
            if ratio > 1.2:
                return "🌟 jelentősen magasabb"
            elif ratio > 1.05:
                return "✅ magasabb"
            elif ratio > 0.95:
                return "➡️ hasonló"
            elif ratio > 0.8:
                return "⚠️ alacsonyabb"
            else:
                return "🔴 jelentősen alacsonyabb"
    
    def get_all_users(self):
        """Összes user ID visszaadása"""
        return sorted(self.df['user_id'].unique())

# Használat
def run_user_eda(df, user_id=None):
    """
    User-specifikus EDA futtatása (csak 1 userre)
    
    Parameters:
    df: DataFrame a tranzakciókkal
    user_id: Vizsgálandó user ID (None esetén random user)
    """
    print("🚀 PÉNZÜGYI ELEMZÉS INDÍTÁSA")
    print(f"Összes felhasználó: {df['user_id'].nunique()} fő")
    
    # EDA objektum létrehozása
    eda = UserFinancialEDA(df)
    
    # User ID meghatározása
    if user_id is None:
        all_users = eda.get_all_users()
        user_id = np.random.choice(all_users)
        print(f"\n🔍 Véletlenszerűen kiválasztott felhasználó: {user_id}")
    
    # Elemzés futtatása
    print("\n" + "="*100)
    print("📊 ELEMZÉS INDÍTÁSA")
    print("="*100)
    
    result = eda.analyze_user(user_id, show_plots=True)
    
    # Összegzés
    print("\n" + "="*100)
    print("✅ ELEMZÉS BEFEJEZVE")
    print("="*100)
    
    return result