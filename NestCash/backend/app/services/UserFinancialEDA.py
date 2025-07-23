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
        self.df['datum'] = pd.to_datetime(self.df['datum'], errors='coerce') 
        
        # Hibás dátumok eltávolítása vagy kezelése
        self.df.dropna(subset=['datum'], inplace=True) # Elhagyjuk a NaT értékeket
        
        # Összeg numerikus konverzió
        self.df['osszeg'] = pd.to_numeric(self.df['osszeg'], errors='coerce')
        self.df.dropna(subset=['osszeg'], inplace=True) # Elhagyjuk a NaT értékeket

        # Bevétel/kiadás szétválasztása
        self.df['is_income'] = self.df['osszeg'] > 0
        self.df['abs_osszeg'] = abs(self.df['osszeg'])
        
        # Időbélyegek hozzáadása
        if not self.df.empty and 'datum' in self.df.columns:
            self.df['ev'] = self.df['datum'].dt.year
            self.df['honap'] = self.df['datum'].dt.to_period('M') 
            self.df['het'] = self.df['datum'].dt.isocalendar().week.astype(int)
            self.df['nap_hete'] = self.df['datum'].dt.dayofweek 
            self.df['nap_hete_nev'] = self.df['datum'].dt.day_name(locale='hu_HU') 
            self.df['ora'] = self.df['datum'].dt.hour # ÚJ: Hozzáadva az óra a temporális elemzéshez
        else:
            print("WARNING: 'datum' oszlop hiányzik vagy DataFrame üres a dátumfeldolgozáshoz.")

        # Rendezés dátum szerint
        self.df.sort_values(by='datum', inplace=True)

    def _get_user_profile(self, user_id_str: str):
        # Ez egy mockup, itt kellene az aktuális user profil adatokat betölteni
        # Pl. adatbázisból vagy egy másik service-ből
        return {
            "user_id": user_id_str,
            "liquid_assets_balance": 100000.0, # Példa érték
            "total_debt": 50000.0 # Példa érték
        }

    def _comparison_text(self, value, benchmark, reverse=False):
        """
        Generál egy összehasonlító szöveget egy érték és egy benchmark alapján.
        Reverse=True esetén kisebb érték a jobb (pl. kiadások).
        """
        if benchmark == 0 and value == 0:
            return "➡️ hasonló"
        if benchmark == 0 and value != 0:
            return "🔴 jelentősen magasabb" if not reverse else "🌟 jelentősen alacsonyabb"
        if benchmark is None or benchmark == 0:
            return "Nincs elegendő összehasonlítási adat"


        ratio = value / benchmark
        if reverse:  # kisebb érték jobb (pl. kiadások, adósság)
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
        else:  # nagyobb érték jobb (pl. bevétel, megtakarítás, vészhelyzeti alap)
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
    
    def _basic_stats_analysis(self, user_data):
        total_income = user_data[user_data['is_income']]['abs_osszeg'].sum()
        total_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
        net_balance = total_income - total_expenses

        if not user_data.empty:
            days_in_period = (user_data['datum'].max() - user_data['datum'].min()).days + 1
            daily_avg_spending = total_expenses / days_in_period if days_in_period > 0 else 0
            
            num_months = user_data['honap'].nunique()
            monthly_avg_spending = total_expenses / num_months if num_months > 0 else 0
        else:
            days_in_period = 0
            daily_avg_spending = 0
            monthly_avg_spending = 0

        # Most aktív nap/óra (kiadások alapján)
        most_active_day_of_week = "N/A"
        most_active_hour = "N/A"
        if not user_data.empty:
            expenses_data = user_data[~user_data['is_income']]
            if not expenses_data.empty:
                if 'nap_hete_nev' in expenses_data.columns:
                    most_active_day_of_week = expenses_data['nap_hete_nev'].mode().iloc[0]
                if 'ora' in expenses_data.columns:
                    most_active_hour = expenses_data['ora'].mode().iloc[0]
        
        return {
            "total_income_huf": total_income,
            "total_expenses_huf": total_expenses,
            "net_balance_huf": net_balance,
            "average_daily_spending_huf": daily_avg_spending,
            "average_monthly_spending_huf": monthly_avg_spending,
            "most_active_day_of_week": most_active_day_of_week,
            "most_active_hour": str(most_active_hour), # Konvertálás stringgé a konzisztencia érdekében
        }

    def _cashflow_analysis(self, user_data):
        total_income = user_data[user_data['is_income']]['abs_osszeg'].sum()
        total_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
        net_balance = total_income - total_expenses

        if not user_data.empty:
            days_in_period = (user_data['datum'].max() - user_data['datum'].min()).days + 1
            daily_avg_spending = total_expenses / days_in_period if days_in_period > 0 else 0
            num_months = user_data['honap'].nunique()
            monthly_avg_spending = total_expenses / num_months if num_months > 0 else 0
        else:
            daily_avg_spending = 0
            monthly_avg_spending = 0
            
        # Havi cashflow
        monthly_flow_dict = {}
        if 'honap' in user_data.columns and not user_data.empty:
            monthly_flow_series = user_data.groupby('honap').apply(
                lambda x: x[x['is_income']]['abs_osszeg'].sum() - x[~x['is_income']]['abs_osszeg'].sum()
            ).rename('monthly_flow')
            
            monthly_flow_dict = {str(period): flow for period, flow in monthly_flow_series.items()}
        
        # Heti cashflow
        weekly_flow_dict = {}
        if 'het' in user_data.columns and not user_data.empty:
            weekly_flow_series = user_data.groupby('het').apply(
                lambda x: x[x['is_income']]['abs_osszeg'].sum() - x[~x['is_income']]['abs_osszeg'].sum()
            ).rename('weekly_flow')
            
            weekly_flow_dict = {str(week_num): flow for week_num, flow in weekly_flow_series.items()}

        # Trend és trendüzenet
        trend = "Stabil"
        trend_msg = "A cashflow stabilan alakul."
        if monthly_flow_dict:
            flows = list(monthly_flow_dict.values())
            if len(flows) >= 2:
                # Egyszerű trend elemzés
                if flows[-1] > flows[-2] * 1.1: # több mint 10% növekedés
                    trend = "Növekvő"
                    trend_msg = "A cashflow pozitív tendenciát mutat, egyre jobban állsz!"
                elif flows[-1] < flows[-2] * 0.9: # több mint 10% csökkenés
                    trend = "Csökkenő"
                    trend_msg = "A cashflow negatív tendenciát mutat, érdemes áttekinteni a kiadásokat."

        return {
            "monthly_flow": monthly_flow_dict,
            "weekly_flow": weekly_flow_dict,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "avg_daily_spending": daily_avg_spending,
            "avg_monthly_spending": monthly_avg_spending,
            "trend": trend, # ÚJ: cashflow trend
            "trend_msg": trend_msg, # ÚJ: cashflow trend üzenet
        }

    def _spending_patterns_analysis(self, user_data):
        monthly_spending_trend = []
        weekly_spending_trend = []
        daily_spending_average = [] # Ezt már máshol is számoljuk, de itt a trend része

        if not user_data.empty:
            # Havi kiadási trend
            if 'honap' in user_data.columns:
                monthly_spending_series = user_data[~user_data['is_income']].groupby('honap')['abs_osszeg'].sum()
                monthly_spending_trend = [{"period": str(period), "amount": amount} for period, amount in monthly_spending_series.items()]

            # Heti kiadási trend
            if 'het' in user_data.columns:
                weekly_spending_series = user_data[~user_data['is_income']].groupby('het')['abs_osszeg'].sum()
                weekly_spending_trend = [{"period": str(week_num), "amount": amount} for week_num, amount in weekly_spending_series.items()]
            
            # Napi átlagos költés naponként (a hét napjai szerint)
            if 'nap_hete_nev' in user_data.columns:
                daily_avg_spending_by_day_of_week = user_data[~user_data['is_income']].groupby('nap_hete_nev')['abs_osszeg'].mean()
                daily_spending_average = [{"day": day, "average_amount": amount} for day, amount in daily_avg_spending_by_day_of_week.items()]

        return {
            "monthly_spending_trend": monthly_spending_trend,
            "weekly_spending_trend": weekly_spending_trend,
            "daily_spending_average": daily_spending_average,
        }

    def _category_analysis(self, user_data):
        user_expenses = user_data[~user_data['is_income']]

        # Top 3 kategória (kiadások)
        top_category_dict = {}
        category_summary_dict = {}
        if not user_expenses.empty and 'kategoria' in user_expenses.columns and 'abs_osszeg' in user_expenses.columns:
            top_category_series = user_expenses.groupby('kategoria')['abs_osszeg'].sum().nlargest(3)
            top_category_dict = top_category_series.to_dict() 
            
            category_summary_series = user_expenses.groupby('kategoria')['abs_osszeg'].sum()
            category_summary_dict = category_summary_series.to_dict() 
            
        # ÚJ: user_categories - megegyezik a category_summary-val
        user_categories_dict = category_summary_dict

        # ÚJ: missing_essentials - placeholder, valós logika hiányában
        missing_essentials_list = [] # Pl. ['Élelmiszer', 'Lakhatás'] ha ezekből nincs kiadás

        # ÚJ: profile_avg_categories - placeholder, valós logika hiányában
        profile_avg_categories_dict = {} # Pl. {'Élelmiszer': 50000, 'Lakhatás': 100000}

        return {
            "top_category": top_category_dict,
            "category_summary": category_summary_dict,
            "user_categories": user_categories_dict,
            "missing_essentials": missing_essentials_list,
            "profile_avg_categories": profile_avg_categories_dict,
        }

    def _temporal_analysis(self, user_data):
        transactions_by_day_of_week = {}
        transactions_by_hour_of_day = {}

        if not user_data.empty:
            # Tranzakciók a hét napjai szerint
            if 'nap_hete_nev' in user_data.columns:
                day_of_week_counts = user_data['nap_hete_nev'].value_counts().to_dict()
                transactions_by_day_of_week = day_of_week_counts
            
            # Tranzakciók a nap órái szerint
            if 'ora' in user_data.columns:
                hour_of_day_counts = user_data['ora'].value_counts().to_dict()
                transactions_by_hour_of_day = {str(hour): count for hour, count in hour_of_day_counts.items()} # Óra szám stringgé konvertálása

        return {
            "transactions_by_day_of_week": transactions_by_day_of_week,
            "transactions_by_hour_of_day": transactions_by_hour_of_day,
        }


    def _risk_analysis(self, user_data, user_profile):
        total_income = user_data[user_data['is_income']]['abs_osszeg'].sum()
        total_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()

        expense_ratio = (total_expenses / total_income) * 100 if total_income > 0 else 100.0
        savings_rate = ((total_income - total_expenses) / total_income) * 100 if total_income > 0 else 0.0

        emergency_fund_months = 0.0
        if user_profile and 'liquid_assets_balance' in user_profile and total_expenses > 0:
            num_months_data = user_data['honap'].nunique()
            if num_months_data > 0:
                avg_monthly_expenses = total_expenses / num_months_data
                if avg_monthly_expenses > 0:
                    emergency_fund_months = user_profile['liquid_assets_balance'] / avg_monthly_expenses
            
        debt_to_income = 0.0
        if user_profile and 'total_debt' in user_profile and total_income > 0:
            debt_to_income = (user_profile['total_debt'] / total_income) * 100

        avg_debt_to_income_benchmark = 36.0 
        avg_emergency_fund_months_benchmark = 4.0 

        debt_to_income_comparison = self._comparison_text(debt_to_income, avg_debt_to_income_benchmark, reverse=True)
        emergency_fund_comparison = self._comparison_text(emergency_fund_months, avg_emergency_fund_months_benchmark, reverse=False)

        # ÚJ: risk_level számítása
        risk_level = "Alacsony"
        if savings_rate < 10 or expense_ratio > 80:
            risk_level = "Magas"
        elif savings_rate < 20 or expense_ratio > 70 or emergency_fund_months < 3 or debt_to_income > 40:
            risk_level = "Közepes"
            
        return {
            "expense_ratio": expense_ratio,
            "savings_rate": savings_rate,
            "debt_to_income": debt_to_income,
            "emergency_fund_months": emergency_fund_months,
            "debt_to_income_comparison": debt_to_income_comparison, 
            "emergency_fund_comparison": emergency_fund_comparison,
            "risk_level": risk_level, # ÚJ: Kockázati szint
        }
    
    def _generate_recommendations(self, user_data, risk_data, user_profile):
        recommendations = []
        
        # Recommendation 1: Savings Rate
        if risk_data['savings_rate'] < 10: 
            recommendations.append({
                "category": "Megtakarítás",
                "advice": f"Jelenlegi megtakarítási rátád: {risk_data['savings_rate']:.1f}%. Próbálj legalább 10-20%-ot félretenni bevételeidből a jövőbeli céljaid eléréséhez.",
                "priority": "Magas"
            })
        elif risk_data['savings_rate'] < 20:
             recommendations.append({
                "category": "Megtakarítás",
                "advice": f"Jelenlegi megtakarítási rátád: {risk_data['savings_rate']:.1f}%. Jó úton haladsz, de a 20% körüli megtakarítási ráta még nagyobb pénzügyi biztonságot nyújthat.",
                "priority": "Közepes"
            })

        # Recommendation 2: Expense Optimization (if expense ratio is high)
        if risk_data['expense_ratio'] > 70: 
            recommendations.append({
                "category": "Költségcsökkentés",
                "advice": f"Kiadásaid aránya a bevételeidhez képest {risk_data['expense_ratio']:.1f}%. Tekintsd át a kiadásaidat, és keress olyan területeket, ahol csökkenteni tudod őket.",
                "priority": "Magas"
            })

        # Recommendation 3: Top Category Optimization
        if risk_data and 'category_analysis' in risk_data and 'top_category' in risk_data['category_analysis'] and risk_data['category_analysis']['top_category']:
            # Find the category with the highest spending (first item if dict not empty)
            top_cat_name = next(iter(risk_data['category_analysis']['top_category'].keys()), None) 
            if top_cat_name:
                top_cat_amount = risk_data['category_analysis']['top_category'][top_cat_name]
                total_expenses = user_data[~user_data['is_income']]['abs_osszeg'].sum()
                
                if total_expenses > 0 and (top_cat_amount / total_expenses) > 0.3: 
                    recommendations.append({
                        "category": "Kategória elemzés",
                        "advice": f"A(z) {top_cat_name} kategória teszi ki kiadásaid jelentős részét. Érdemes lehet megvizsgálni, hogyan csökkentheted az ehhez kapcsolódó költségeidet.",
                        "priority": "Közepes"
                    })
        
        # Recommendation 4: Emergency Fund (if low)
        if risk_data['emergency_fund_months'] < 3: 
            recommendations.append({
                "category": "Vészhelyzeti alap",
                "advice": f"Jelenlegi vészhelyzeti alapod mindössze {risk_data['emergency_fund_months']:.1f} hónapnyi kiadást fedez. Célként tűzz ki legalább 3-6 hónapnyi kiadásnak megfelelő összeget.",
                "priority": "Magas"
            })
            
        # Recommendation 5: Debt (if high)
        if risk_data['debt_to_income'] > 40: 
            recommendations.append({
                "category": "Adósság",
                "advice": f"Adósság/bevétel arányod {risk_data['debt_to_income']:.1f}%. Az adósság csökkentése javíthatja pénzügyi helyzetedet és rugalmasságodat.",
                "priority": "Magas"
            })

        return recommendations


    def analyze_user(self, user_id_str: str, show_plots: bool = False):
        user_data = self.df[self.df['user_id'] == user_id_str].copy()
        
        # Alapértelmezett üres/hiányzó adatok eredmény struktúra
        default_empty_analysis_result = {
            "user_id": user_id_str,
            "time_period": "Nincs elegendő adat",
            "transaction_count": 0,
            "basic_stats": {
                "total_income_huf": 0.0,
                "total_expenses_huf": 0.0,
                "net_balance_huf": 0.0,
                "average_daily_spending_huf": 0.0,
                "average_monthly_spending_huf": 0.0,
                "most_active_day_of_week": "N/A",
                "most_active_hour": "N/A",
            },
            "cashflow": {
                "monthly_flow": {},
                "weekly_flow": {},
                "total_income": 0.0,
                "total_expenses": 0.0,
                "net_balance": 0.0,
                "avg_daily_spending": 0.0,
                "avg_monthly_spending": 0.0,
                "trend": "Nincs elegendő adat",
                "trend_msg": "Nincs elegendő adat",
            },
            "spending_patterns": {
                "monthly_spending_trend": [],
                "weekly_spending_trend": [],
                "daily_spending_average": [],
            },
            "category_analysis": {
                "top_category": {},
                "category_summary": {},
                "user_categories": {},
                "missing_essentials": [],
                "profile_avg_categories": {},
            },
            "temporal_analysis": {
                "transactions_by_day_of_week": {},
                "transactions_by_hour_of_day": {},
            },
            "risk_analysis": {
                "expense_ratio": 0.0,
                "savings_rate": 0.0,
                "debt_to_income": 0.0, 
                "emergency_fund_months": 0.0,
                "debt_to_income_comparison": "Nincs elegendő adat",
                "emergency_fund_comparison": "Nincs elegendő adat",
                "risk_level": "Alacsony",
            },
            "recommendations": [
                {"category": "Általános", "advice": "Nincs elegendő adat az elemzéshez.", "priority": "Alacsony"}
            ]
        }

        # Kezeljük az eseteket, amikor nincs adat
        if user_data.empty:
            return default_empty_analysis_result

        # Ellenőrzés: legalább 7 napnyi tranzakciós előzmény
        first_transaction_date = user_data['datum'].min()
        last_transaction_date = user_data['datum'].max()
        time_difference = last_transaction_date - first_transaction_date

        if time_difference.days < 7:
            # Frissítjük a javaslatot a 7 napos limit miatt
            insufficient_data_result = default_empty_analysis_result.copy()
            insufficient_data_result['recommendations'] = [
                {"category": "Általános", "advice": "Legalább 7 napnyi tranzakciós előzmény szükséges.", "priority": "Magas"}
            ]
            return insufficient_data_result

        # Ha elegendő adat van, futtassuk a teljes elemzést
        user_profile = self._get_user_profile(user_id_str)
        
        basic_stats_data = self._basic_stats_analysis(user_data)
        cashflow_data = self._cashflow_analysis(user_data)
        spending_patterns_data = self._spending_patterns_analysis(user_data)
        category_data = self._category_analysis(user_data)
        temporal_analysis_data = self._temporal_analysis(user_data)
        risk_data = self._risk_analysis(user_data, user_profile) 
        recommendations = self._generate_recommendations(user_data, risk_data, user_profile) 

        analysis_result = {
            "user_id": user_id_str, 
            "time_period": f"{first_transaction_date.strftime('%Y.%m.%d')} - {last_transaction_date.strftime('%Y.%m.%d')}",
            "transaction_count": user_data.shape[0],
            "basic_stats": basic_stats_data,
            "cashflow": cashflow_data,
            "spending_patterns": spending_patterns_data,
            "category_analysis": category_data,
            "temporal_analysis": temporal_analysis_data,
            "risk_analysis": risk_data,
            "recommendations": recommendations
        }
        
        return analysis_result


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
    eda = UserFinancialEDA(df)
    
    if user_id:
        target_user_id = user_id
    else:
        all_users = eda.get_all_users()
        if not all_users:
            print("Nincs elérhető felhasználó az adatokban.")
            return
        target_user_id = all_users[0] # Válasszuk az első felhasználót, ha nincs megadva
        print(f"Nincs megadva user ID, elemzés a következő felhasználóval: {target_user_id}")
            
    analysis_result = eda.analyze_user(target_user_id)
    return analysis_result