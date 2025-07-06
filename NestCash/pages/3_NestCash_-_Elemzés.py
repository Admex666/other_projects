# pages/3_📊_Pénzügyi_elemzés.py
import streamlit as st
import pandas as pd
from PenzugyiElemzo import PenzugyiElemzo
from UserFinancialEDA import UserFinancialEDA, run_user_eda
from MLinsight import MLinsight
import plotly.express as px

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
with st.expander("🔄 Cashflow Elemzés"):
    tab1, tab2, tab3 = st.tabs(["Bevételek", "Kiadások", "Trendek"])
    
    with tab1:
        col1, col2 = st.columns(2)
        col1.metric("💰 Átlag havi bevétel", f"{eredmenyek['basic_stats']['user_income']/honapok:,.0f} Ft",
                   f"hasonló profil: {eredmenyek['basic_stats']['benchmark_income']/honapok:,.0f} Ft",
                   delta_color="off")
        col2.metric("🏆 Jövedelem rangsor", f"Top {eredmenyek['basic_stats']['user_rank_income']:.1f}%")
        
    with tab2:
        st.subheader("Kiadási szerkezet")
        col1, col2 = st.columns(2)
        col1.metric("🧾 Fix költségek", f"{eredmenyek['spending_patterns']['fixed_costs']/honapok:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['fixed_ratio']:.1f}%", 
                   delta_color="inverse")
        col2.metric("🎭 Változó költségek", f"{eredmenyek['spending_patterns']['variable_costs']/honapok:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['variable_ratio']:.1f}%",
                   delta_color="inverse")
        
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
        for rank in sorted(eredmenyek['category_analysis']['top_category'].keys())[:3]:
            cat = eredmenyek['category_analysis']['top_category'][rank]
            st.write(f"{rank}. {cat['name']}: {cat['amount']:,.0f} Ft")
            
    with tab3:
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
                    "Napi átlagos tempó", 
                    f"{abs(data['daily_difference']):,.0f} Ft",
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
        col2.metric("🏅 Megtakarítás rangsor", f"Top {eredmenyek['basic_stats']['user_rank_savings']:.1f}%")
        
        st.subheader("Tartalék elemzés")
        runway = jelentés["cash_flow_elemzes"]['runway'].get('runway_honapok', {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Készpénzfedezet", f"{runway.get('csak_keszpenz', 'N/A')} hónap")
        col2.metric("Teljes fedezet", f"{runway.get('osszes_asset', 'N/A')} hónap")
        col3.metric("Ajánlott", "3-6 hónap")
    
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

# 4. GÉPI TANULÁS ÉLMEZÉNYEK
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