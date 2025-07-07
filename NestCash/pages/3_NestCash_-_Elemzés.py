# pages/3_📊_Pénzügyi_elemzés.py
import streamlit as st
import pandas as pd
from PenzugyiElemzo import PenzugyiElemzo
from UserFinancialEDA import UserFinancialEDA, run_user_eda
from MLinsight import MLinsight
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

def run_whatif_analysis(current_user, df, scenarios):
    """
    What-If elemzés futtatása különböző forgatókönyvekkel
    """
    results = {}
    user_df = df[df["user_id"] == current_user]
    
    # Jelenlegi alapadatok
    current_monthly_income = user_df[user_df['bev_kiad_tipus'] == 'bevetel']['osszeg'].sum() / len(user_df['honap'].unique())
    current_monthly_expenses = abs(user_df[user_df['bev_kiad_tipus'] != 'bevetel']['osszeg'].sum()) / len(user_df['honap'].unique())
    current_savings_rate = (current_monthly_income - current_monthly_expenses) / current_monthly_income if current_monthly_income > 0 else 0
    
    # Jelenlegi vagyonelemek
    current_liquid = user_df['likvid'].iloc[-1] if not user_df.empty else 0
    current_investments = user_df['befektetes'].iloc[-1] if not user_df.empty else 0
    current_savings = user_df['megtakaritas'].iloc[-1] if not user_df.empty else 0
    
    for scenario_name, scenario in scenarios.items():
        # Módosított paraméterek
        new_income = current_monthly_income * (1 + scenario['income_change'])
        new_expenses = current_monthly_expenses * (1 + scenario['expense_change'])
        new_monthly_savings = (new_income - new_expenses) + scenario.get('extra_monthly_savings', 0)
        
        # Idősorok generálása
        months = scenario['months']
        timeline = []
        liquid_timeline = []
        investment_timeline = []
        total_timeline = []
        
        liquid = current_liquid
        investments = current_investments
        savings = current_savings
        
        investment_return = scenario.get('investment_return', 0.07) / 12  # havi hozam
        
        for month in range(months):
            timeline.append(month)
            
            # Havi megtakarítás allokálása
            if new_monthly_savings > 0:
                liquid += new_monthly_savings * scenario.get('liquid_allocation', 0.3)
                investments += new_monthly_savings * scenario.get('investment_allocation', 0.4)
                savings += new_monthly_savings * scenario.get('savings_allocation', 0.3)
            
            # Befektetések hozama
            investments *= (1 + investment_return)
            
            liquid_timeline.append(liquid)
            investment_timeline.append(investments)
            total_timeline.append(liquid + investments + savings)
        
        # Konfidencia intervallumok (Monte Carlo szimuláció egyszerűsített változata)
        volatility = scenario.get('volatility', 0.1)
        confidence_intervals = []
        
        for month in range(months):
            base_value = total_timeline[month]
            std_dev = base_value * volatility * np.sqrt(month / 12)  # idővel növekvő volatilitás
            
            # 95% konfidencia intervallum
            lower_bound = base_value - 1.96 * std_dev
            upper_bound = base_value + 1.96 * std_dev
            
            confidence_intervals.append({
                'month': month,
                'lower': max(0, lower_bound),  # nem lehet negatív
                'upper': upper_bound,
                'base': base_value
            })
        
        results[scenario_name] = {
            'timeline': timeline,
            'liquid': liquid_timeline,
            'investments': investment_timeline,
            'total': total_timeline,
            'confidence_intervals': confidence_intervals,
            'final_total': total_timeline[-1],
            'monthly_savings': new_monthly_savings,
            'new_income': new_income,
            'new_expenses': new_expenses
        }
    
    return results


# --- INIT ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

# --- HEADER ---
st.title("💰 NestCash prototípus")
st.success(f"👤 Bejelentkezve mint: {st.session_state.username} (ID: {current_user})")

# --- QUICK SUMMARY CARDS ---
cols = st.columns(3)
likvid = user_df['likvid'].iloc[-1] if not user_df.empty else 0
befektetes = user_df['befektetes'].iloc[-1] if not user_df.empty else 0
megtakaritas = user_df['megtakaritas'].iloc[-1] if not user_df.empty else 0

cols[0].metric("💵 Likvid", f"{likvid:,.0f}Ft")
cols[1].metric("📈 Befektetések", f"{befektetes:,.0f}Ft")
cols[2].metric("🏦 Megtakarítások", f"{megtakaritas:,.0f}Ft")

# --- MAIN ANALYSIS ---
if len(df) < 20 or len(user_df) < 20:
    st.warning("Nincs elég adat az elemzéshez. Kérjük, adj hozzá új tranzakciókat.")
    st.stop()

eredmenyek = run_user_eda(df, current_user)
elemzo = PenzugyiElemzo(df)
jelentés = elemzo.generate_comprehensive_report(current_user)
ml_insight = MLinsight(df, current_user)
honapok = len(user_df.honap.unique())


# 1. ÁTTEKINTŰ IRÁNYTŰ
with st.expander("🎯 Pénzügyi Egészség - Gyorsjelentés", expanded=True):
    st.metric("📅 Időszak", f"{eredmenyek['time_period']['start']} - {eredmenyek['time_period']['end']}")
    # Health meter visual
    health_score = int(jelentés['executive_summary'].get('penzugyi_egeszseg_pontszam', 0))
    st.progress(health_score/100, text=f"💖 Pénzügyi Egészség pontszám: {health_score}%")

    st.metric("📊 Állapot", jelentés["executive_summary"].get('altalanos_ertekeles', 'N/A'))
    
# 2. BEVÉTELEK & KIADÁSOK
with st.expander("🔄 Pénzmozgás Elemzés"):
    tab1, tab2 = st.tabs(["Bevételek és Kiadások", "Trendek"])
    
    with tab1:
        st.subheader("Bevételek")
        st.metric("💰 Átlag havi bevétel", f"{eredmenyek['basic_stats']['user_income']/honapok:,.0f} Ft",
                   f"hasonló profil: {eredmenyek['basic_stats']['benchmark_income']/honapok:,.0f} Ft",
                   delta_color="off")
        
        st.subheader("Kiadási szerkezet")
        col1, col2 = st.columns(2)
        col1.metric("🧾 Fix költségek", f"{eredmenyek['spending_patterns']['fixed_costs']/honapok:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['fixed_ratio']:.1f}%-a az összesnek", 
                   delta_color="off")
        col2.metric("🎭 Változó költségek", f"{eredmenyek['spending_patterns']['variable_costs']/honapok:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['variable_ratio']:.1f}%-a az összesnek",
                   delta_color="off")
        
        st.subheader("Kategóriákra bontva")
        
        # Sunburst chart előkészítése
        category_data = []
        for rank, cat in eredmenyek['category_analysis']['top_category'].items():
            category_data.append({
                'category': cat['name'],
                'amount': cat['amount'],
                'percentage': cat['percentage']
            })
        
        # Két szintű hierarchia (fő és alkategóriák) - példa, módosítsd a valós adatokhoz
        # Ez feltételezi, hogy van fő és alkategória szétválasztás (pl. "élelmiszer-tejtermékek")
        # Ha nincs, akkor csak a fő kategóriákat használd
        df_sunburst = pd.DataFrame(category_data)
        df_sunburst['main_category'] = df_sunburst['category'].apply(lambda x: x.split('-')[0] if '-' in x else x)
        df_sunburst['subcategory'] = df_sunburst['category'].apply(lambda x: x.split('-')[1] if '-' in x else "Egyéb")
        
        # Sunburst chart létrehozása
        fig = px.sunburst(
            df_sunburst,
            path=['main_category'],
            values='amount',
            color='main_category',
            hover_data=['percentage'],
            title='Kiadások eloszlása'
        )
        fig.update_traces(textinfo="label+percent parent")
        st.plotly_chart(fig, use_container_width=True)
        
        # Régi progress bar-ok helyett csak a top3 kategória
        st.write("**Legnagyobb kiadási kategóriák:**")
        with st.container(border=True):
            for rank in sorted(eredmenyek['category_analysis']['top_category'].keys())[:5]:
                cat = eredmenyek['category_analysis']['top_category'][rank]
                st.write(f"{rank}. {cat['name']}: {cat['amount']:,.0f} Ft")
            
    with tab2:
        st.line_chart(pd.DataFrame.from_dict(eredmenyek['cashflow']['monthly_flow'], 
                     orient='index', columns=['Havi nettó']))
        st.write(f"**Trend:** {eredmenyek['cashflow']['trend_msg']}")
        
with st.expander("📅 Havi korlátok haladása", expanded=True):
    from database import calculate_monthly_progress
    from datetime import datetime
    
    current_month = datetime.now().strftime("%Y-%m")
    progress_data = calculate_monthly_progress(current_user, current_month)
    
    if progress_data:
        # Kategóriánként megjelenítés
        for category, data in progress_data.items():
            with st.container():
                st.write(f"### {category.capitalize()}")
                
                # Színkódolás a haladás alapján
                if data["limit_type"] == "maximum":
                    # Kiadási korlát
                    if data["current_amount"] > data["limit_amount"]:
                        status_color = "🔴"
                        status_text = "Túllépve"
                    elif data["current_amount"] > data["limit_amount"] * 0.8:
                        status_color = "🟡"
                        status_text = "Közel a korláthoz"
                    else:
                        status_color = "🟢"
                        status_text = "Rendben"
                else:
                    # Bevételi minimum
                    if data["current_amount"] < data["limit_amount"]:
                        status_color = "🔴"
                        status_text = "Alatta"
                    elif data["current_amount"] < data["limit_amount"] * 1.2:
                        status_color = "🟡"
                        status_text = "Közel a célhoz"
                    else:
                        status_color = "🟢"
                        status_text = "Cél elérve"
                
                # Metrikák megjelenítése
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(
                    f"{status_color} Jelenlegi", 
                    f"{data['current_amount']:,.0f} Ft",
                    f"{data['progress_percentage']:.1f}%"
                )
                
                col2.metric(
                    "Havi korlát/cél", 
                    f"{data['limit_amount']:,.0f} Ft",
                    f"{data['limit_type']}"
                )
                
                if data["limit_type"] == "maximum":
                    col3.metric(
                        "Még elkölthető", 
                        f"{max(0, data['remaining']):,.0f} Ft",
                        f"{status_text}"
                    )
                else:
                    col3.metric(
                        "Még szükséges", 
                        f"{max(0, -data['remaining']):,.0f} Ft",
                        f"{status_text}"
                    )
                
                # Napi elemzés
                daily_status = "🔴⬆️ Túl gyors" if data["daily_difference"] > 0 else "🟢⬇ Alacsony"
                if abs(data["daily_difference"]) < data["limit_amount"] * 0.1:
                    daily_status = "➡️ Ideális"
                
                col4.metric(
                    "Eltérés napi átlagos tempótól", 
                    f"{abs(data['daily_difference']):+,.0f} Ft",
                    daily_status
                )
                
                # Progress bar
                progress_value = min(data["progress_percentage"] / 100, 1.0)
                if data["limit_type"] == "maximum":
                    st.progress(progress_value, 
                              text=f"Felhasználva: {data['current_amount']:,.0f} Ft / {data['limit_amount']:,.0f} Ft")
                else:
                    st.progress(progress_value, 
                              text=f"Teljesítve: {data['current_amount']:,.0f} Ft / {data['limit_amount']:,.0f} Ft")
                
                # Részletes napi elemzés
                with st.expander(f"Részletes napi elemzés - {category}"):
                    st.write(f"**Ideális összeg:** {data['daily_ideal']:,.0f} Ft")
                    st.write(f"**Eltérés az ideálistól:** {data['daily_difference']:+,.0f} Ft")
                    
                    if data["limit_type"] == "maximum":
                        if data["daily_difference"] > 0:
                            st.warning(f"🚨 Túllépted az átlagos költési tempót! {data['daily_difference']:,.0f} Ft-tal több, mint az ideális napi összeg.")
                        else:
                            st.success(f"👍 Jó tempó! {abs(data['daily_difference']):,.0f} Ft-tal kevesebb, mint az ideális napi összeg.")
                    else:
                        if data["daily_difference"] > 0:
                            st.warning(f"🚨 Lassú tempó! {data['daily_difference']:,.0f} Ft-tal kevesebb, mint az ideális napi összeg.")
                        else:
                            st.success(f"👍 Jó tempó! {abs(data['daily_difference']):,.0f} Ft-tal több, mint az ideális napi összeg.")
                
                st.divider()
    else:
        st.info("Nincsenek beállított havi korlátok. Állíts be korlátokat a Tranzakciók oldalon!")

# 3. MEGTAKARÍTÁS & BEFEKTETÉS
with st.expander("🚀 Jövőtervezés"):
    tab1, tab2 = st.tabs(["Megtakarítás", "Befektetés"])
    
    with tab1:
        col1, col2 = st.columns(2)
        col1.metric("💎 Megtakarítási ráta", f"{eredmenyek['basic_stats']['user_savings_rate']:.1f}%",
                   f"átlag: {eredmenyek['basic_stats']['benchmark_savings_rate']:.1f}%",
                   delta_color="off")
        
        st.subheader("Tartalék elemzés")
        runway = jelentés["cash_flow_elemzes"]['runway'].get('runway_honapok', {})
        col1, col2 = st.columns(2)
        col1.metric("Készpénzfedezet", f"{runway.get('csak_keszpenz', 'N/A')} hónap")
        col2.metric("Teljes vagyon fedezet", f"{runway.get('osszes_asset', 'N/A')} hónap")
        st.info("3-6 hónapnyi tartalék ajánlott a hirtelen kiadások fedezésére.")
        
    with tab2:
        st.subheader("Portfólió állapot")
        col1, col2 = st.columns(2)
        
        assets = jelentés["befektetesi_elemzes"]['portfolio_suggestions'].get('jelenlegi_allokaciok', {}).keys()
        with col1:
            st.write("#### Jelenlegi")
            for asset in assets:
                pct = jelentés["befektetesi_elemzes"]['portfolio_suggestions'].get('jelenlegi_allokaciok', {})[asset]
                st.metric(asset, f"{pct:.0f}%")
        
        with col2:
            st.write("#### Javasolt")
            for asset in assets:
                pct = jelentés["befektetesi_elemzes"]['portfolio_suggestions'].get('javasolt_allokaciok', {})[asset]
                st.metric(asset, f"{pct:.0f}%", 
                          delta=f"{pct - jelentés['befektetesi_elemzes']['portfolio_suggestions']['jelenlegi_allokaciok'].get(asset,0):+.0f}%pont")

# 4. GÉPI TANULÁS ELEMZÉSEK
with st.expander("🤖 Intelligens elemzések"):
    tab1, tab2 = st.tabs(["Kockázat", "Trendek"])
    
    with tab1:
        if "nem kerülsz mínuszba" in ml_insight['risk_msg']:
            st.success(ml_insight['risk_msg'])
        else:
            st.error(ml_insight['risk_msg'])
        
        st.subheader("Költési minták")
        col1, col2 = st.columns(2)
        col1.metric("Impulzusvásárlások", f"{eredmenyek['spending_patterns']['user_impulse_pct']:.1f}%",
                   f"átlag: {eredmenyek['spending_patterns']['profile_impulse_pct']:.1f}%",
                   delta_color="off")
        col2.metric("Költési diverzitás", f"{ml_insight['diversity']['div_user']:.4f}",
                   f"átlag: {ml_insight['diversity']['div_benchmark']:.4f}",
                   delta_color="off")
    
    with tab2:
        st.subheader("Napi átlagos költések")
        cols = st.columns(3)
        roll7 = abs(ml_insight['rolling_avg']['roll7'])
        cols[0].metric("Legutóbbi 7 napban", f"{roll7:,.0f} Ft",
                       f"hetente: {7*roll7:,.0f} Ft", delta_color='off')
        roll30 = abs(ml_insight['rolling_avg']['roll30'])
        cols[1].metric("Legutóbbi 30 napban", f"{roll30:,.0f} Ft",
                       f"hetente: {7*roll30:,.0f} Ft", delta_color='off')
        roll90 = abs(ml_insight['rolling_avg']['roll90'])
        cols[2].metric("Legutóbbi 90 napban", f"{roll90:,.0f} Ft",
                       f"hetente: {7*roll90:,.0f} Ft", delta_color='off')
        
        st.metric("Megtakarítások változása", f"{ml_insight['savings_trend_pp']:.1%}pont")

# 5. JAVASLATOK & AKCIÓK
with st.expander("💡 Optimalizálási lehetőségek", expanded=True):
    st.subheader("🔎 Pareto elemzés")
    st.write(f"A kiadások {jelentés['sporolas_optimalizacio']['pareto_analysis'].get('pareto_arany_pct', 'N/A')}%-a "
             f"{len(jelentés['sporolas_optimalizacio']['pareto_analysis'].get('pareto_kategoriak', []))} kategóriából származik")
    
    st.subheader("🚀 Cselekvési pontok")
    for rec in eredmenyek['recommendations']:
        st.write(f"- {rec}")
    
    if st.button("🧮 Indíts egy spórolás szimulációt!"):
        st.session_state.show_simulator = True

if st.session_state.get('show_simulator', False):
    with st.expander("🎮 Spórolás Szimulátor", expanded=True):
        st.subheader("Szimulálj különböző forgatókönyveket!")
        col1, col2 = st.columns(2)
        with col1:
            extra_saving = st.number_input("Havi extra megtakarítás (Ft)", 0)
        with col2:
            return_rate = st.slider("Várható hozam (%/év)", 0.0, 15.0, 7.0, 0.5)
        
        years = st.slider("Évek száma", 1, 20, 5)
        
        total = extra_saving * 12 * years
        compounded = extra_saving * (((1 + return_rate/100)**years - 1) / (return_rate/100)) * 12
        
        if st.button("Számold ki"):
            st.metric("Összes megtakarítás", f"{total:,.0f} Ft")
            st.metric("Kamatos kamattal", f"{compounded:,.0f} Ft", 
                     delta=f"+{(compounded-total):,.0f} Ft")

# 6. WHAT-IF ELEMZÉS
with st.expander("🔮 What-If Elemzés", expanded=True):
    st.subheader("Tervezd meg a jövődet - különböző forgatókönyvekkel!")
    
    # Első lépés: Forgatókönyv választása
    st.write("#### 🎯 Forgatókönyv választása")
    
    scenarios_quick = {
        "Konzervatív": {"income": 0, "expense": 0, "extra": 20000, "return": 0.04},
        "Kiegyensúlyozott": {"income": 0.05, "expense": 0, "extra": 50000, "return": 0.07},
        "Agresszív": {"income": 0.1, "expense": -0.1, "extra": 100000, "return": 0.12},
        "Krízis": {"income": -0.2, "expense": 0.1, "extra": 0, "return": 0.02}
    }
    
    selected_scenario = st.selectbox("Válassz forgatókönyvet", 
                                   ["Egyéni beállítás"] + list(scenarios_quick.keys()))
    
    # Forgatókönyv leírása
    scenario_descriptions = {
        "Konzervatív": "Biztonságos megközelítés alacsony kockázattal és stabil hozammal",
        "Kiegyensúlyozott": "Mérsékelt kockázat és közepes hozamelvárás",
        "Agresszív": "Magas kockázat, magas hozamelvárás",
        "Krízis": "Gazdasági nehézségek modellezése",
        "Egyéni beállítás": "Saját paraméterek megadása"
    }
    
    st.info(f"**{selected_scenario}:** {scenario_descriptions[selected_scenario]}")
    
    # Forgatókönyv beállítások
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📊 Paraméterek")
        
        # Alapbeállítások
        analysis_months = st.slider("Elemzési időszak (hónap)", 3, 60, 12)
        
        # Ha előre definiált forgatókönyv van kiválasztva, akkor azok az értékek
        if selected_scenario != "Egyéni beállítás":
            scenario = scenarios_quick[selected_scenario]
            default_income = int(scenario["income"] * 100)
            default_expense = int(scenario["expense"] * 100)
            default_extra = scenario["extra"]
            default_return = scenario["return"] * 100
            
            # Csak olvasható megjelenítés
            st.info(f"**{selected_scenario} forgatókönyv alkalmazva:**")
            st.write(f"- Jövedelem változás: {default_income}%")
            st.write(f"- Kiadás változás: {default_expense}%")
            st.write(f"- Extra megtakarítás: {default_extra:,} Ft")
            st.write(f"- Várható hozam: {default_return:.1f}%")
            
            # Értékek beállítása
            income_change = scenario["income"]
            expense_change = scenario["expense"]
            extra_savings = scenario["extra"]
            investment_return = scenario["return"]
            
        else:
            # Egyéni beállításoknál a sliderek aktívak
            st.write("Állítsd be a paramétereket:")
            
            # Jövedelem változás
            income_change = st.slider("Jövedelem változás (%)", -50, 100, 0) / 100
            
            # Kiadás változás
            expense_change = st.slider("Kiadások változása (%)", -50, 50, 0) / 100
            
            # Extra megtakarítás
            extra_savings = st.number_input("Extra havi megtakarítás (Ft)", 0, 500000, 0)
            
            # Befektetési hozam
            investment_return = st.slider("Várható éves hozam (%)", 0.0, 20.0, 7.0) / 100
        
        # Volatilitás mindig beállítható
        volatility = st.slider("Piaci ingadozás (%)", 0.0, 30.0, 10.0) / 100
    
    with col2:
        st.write("#### 💰 Allokáció")
        
        # Megtakarítások allokálása
        liquid_alloc = st.slider("Likvid eszközök (%)", 0, 100, 30) / 100
        investment_alloc = st.slider("Befektetések (%)", 0, 100, 40) / 100
        savings_alloc = st.slider("Megtakarítások (%)", 0, 100, 30) / 100
        
        # Ellenőrzés
        total_alloc = liquid_alloc + investment_alloc + savings_alloc
        if abs(total_alloc - 1.0) > 0.01:
            st.warning(f"⚠️ Az allokáció összege {total_alloc:.0%} (nem 100%)")
    
    # Forgatókönyv összeállítása
    scenario_config = {
        "Választott forgatókönyv": {
            'income_change': income_change,
            'expense_change': expense_change,
            'extra_monthly_savings': extra_savings,
            'investment_return': investment_return,
            'volatility': volatility,
            'months': analysis_months,
            'liquid_allocation': liquid_alloc,
            'investment_allocation': investment_alloc,
            'savings_allocation': savings_alloc
        }
    }
    
    # Összehasonlítás a jelenlegi helyzettel
    scenario_config["Jelenlegi trend"] = {
        'income_change': 0,
        'expense_change': 0,
        'extra_monthly_savings': 0,
        'investment_return': 0.03,  # alacsony alap hozam
        'volatility': 0.05,
        'months': analysis_months,
        'liquid_allocation': 0.5,
        'investment_allocation': 0.3,
        'savings_allocation': 0.2
    }
    
    if st.button("🚀 Elemzés futtatása"):
        # What-If elemzés futtatása
        results = run_whatif_analysis(current_user, df, scenario_config)
        
        # Eredmények megjelenítése
        st.subheader("📈 Eredmények")
        
        # Összefoglaló metrikák
        col1, col2, col3 = st.columns(3)
        
        chosen_result = results["Választott forgatókönyv"]
        current_result = results["Jelenlegi trend"]
        
        col1.metric(
            "Várható vagyon", 
            f"{chosen_result['final_total']:,.0f} Ft",
            f"{chosen_result['final_total'] - current_result['final_total']:+,.0f} Ft"
        )
        
        col2.metric(
            "Havi megtakarítás",
            f"{chosen_result['monthly_savings']:,.0f} Ft",
            f"{chosen_result['monthly_savings'] - current_result['monthly_savings']:+,.0f} Ft"
        )
        
        col3.metric(
            "Megtakarítási ráta",
            f"{chosen_result['monthly_savings']/chosen_result['new_income']:.1%}" if chosen_result['new_income'] > 0 else "N/A",
            f"{(chosen_result['monthly_savings']/chosen_result['new_income'] - current_result['monthly_savings']/current_result['new_income']):.1%}pont" if chosen_result['new_income'] > 0 and current_result['new_income'] > 0 else ""
        )
        
        # Interaktív grafikon
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Összesített vagyon alakulása', 'Vagyonelemek összetétele', 
                          'Becslési tartományok', 'Havi cash flow'),
            specs=[[{"secondary_y": False}, {"type": "pie"}],
                   [{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # 1. Összesített vagyon alakulása
        for scenario_name, result in results.items():
            fig.add_trace(
                go.Scatter(
                    x=result['timeline'],
                    y=result['total'],
                    name=scenario_name,
                    mode='lines+markers'
                ),
                row=1, col=1
            )
        
        # 2. Vagyonelemek összetétele (utolsó hónap)
        chosen_result = results["Választott forgatókönyv"]
        fig.add_trace(
            go.Pie(
                values=[chosen_result['liquid'][-1], chosen_result['investments'][-1], 
                       chosen_result['final_total'] - chosen_result['liquid'][-1] - chosen_result['investments'][-1]],
                labels=['Likvid', 'Befektetések', 'Megtakarítások'],
                name="Portfólió"
            ),
            row=1, col=2
        )
        
        # 3. Konfidencia intervallumok
        conf_intervals = chosen_result['confidence_intervals']
        
        # Alsó határ
        fig.add_trace(
            go.Scatter(
                x=[ci['month'] for ci in conf_intervals],
                y=[ci['lower'] for ci in conf_intervals],
                name='Alsó határ (95%)',
                line=dict(color='rgba(255,0,0,0.3)'),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Felső határ
        fig.add_trace(
            go.Scatter(
                x=[ci['month'] for ci in conf_intervals],
                y=[ci['upper'] for ci in conf_intervals],
                name='Felső határ (95%)',
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(0,100,80,0.3)'),
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Várható érték
        fig.add_trace(
            go.Scatter(
                x=[ci['month'] for ci in conf_intervals],
                y=[ci['base'] for ci in conf_intervals],
                name='Várható érték',
                line=dict(color='blue', width=3)
            ),
            row=2, col=1
        )
        
        # 4. Havi cash flow
        monthly_cashflow = [chosen_result['monthly_savings']] * len(chosen_result['timeline'])
        fig.add_trace(
            go.Bar(
                x=chosen_result['timeline'],
                y=monthly_cashflow,
                name='Havi nettó megtakarítás',
                marker_color='green' if chosen_result['monthly_savings'] > 0 else 'red'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="What-If Elemzés - Részletes Eredmények",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Kockázati értékelés
        st.subheader("⚠️ Kockázati értékelés")
        
        # Számítsuk ki a valószínűségeket
        negative_months = sum(1 for ci in conf_intervals if ci['lower'] < 0)
        probability_loss = negative_months / len(conf_intervals) * 100
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric(
            "Veszteség kockázata",
            f"{probability_loss:.1f}%",
            "A portfólió értéke a becslési tartomány alapján"
        )
        
        volatility_score = chosen_result['confidence_intervals'][-1]['upper'] - chosen_result['confidence_intervals'][-1]['lower']
        col2.metric(
            "Ingadozás",
            f"{volatility_score:,.0f} Ft",
            "Becsült tartomány szélessége"
        )
        
        # Stressz teszt
        stress_scenario = chosen_result['confidence_intervals'][-1]['lower']
        col3.metric(
            "Stressz teszt",
            f"{stress_scenario:,.0f} Ft",
            "Legrosszabb esetben várható vagyon"
        )
        
        # Akciós javaslatok
        st.subheader("💡 Személyre szabott javaslatok")
        
        if chosen_result['monthly_savings'] < 0:
            st.error("🚨 Negatív megtakarítási ráta! Csökkentsd a kiadásokat vagy növeld a bevételeket.")
        elif chosen_result['monthly_savings'] < 50000:
            st.warning("⚠️ Alacsony megtakarítási ráta. Próbálj meg legalább 50.000 Ft-ot havonta megtakarítani.")
        else:
            st.success("✅ Egészséges megtakarítási ráta!")
        
        if probability_loss > 20:
            st.error("🚨 Magas kockázat! Fontold meg a konzervatívabb befektetési stratégiát.")
        elif probability_loss > 10:
            st.warning("⚠️ Közepes kockázat. Diverzifikáld a portfóliódat.")
        else:
            st.success("✅ Alacsony kockázat!")