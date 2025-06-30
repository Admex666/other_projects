# pages/3_📊_Pénzügyi_elemzés.py
import streamlit as st
import pandas as pd
from PenzugyiElemzo import PenzugyiElemzo
from UserFinancialEDA import UserFinancialEDA, run_user_eda
from MLinsight import MLinsight

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

st.title("📊 Pénzügyi elemzés")

if not (len(df) < 20) and not (len(user_df) < 20):
    eredmenyek = run_user_eda(df, current_user)
    elemzo = PenzugyiElemzo(df)
    jelentés = elemzo.generate_comprehensive_report(current_user)
    ml_insight = MLinsight(df, current_user)
    
    honapok = len(user_df.honap.unique())
    
    # 1. Alapadatok és összefoglaló
    st.subheader("📌 Alapadatok")
    st.metric("Időszak", f"{eredmenyek['time_period']['start']} - {eredmenyek['time_period']['end']}")
    
    # Executive Summary
    st.subheader("📊 Összefoglaló")
    exec_summary = jelentés["executive_summary"]
    st.write(f"**Pénzügyi egészség pontszám:** {exec_summary.get('penzugyi_egeszseg_pontszam', 'N/A')}")
    st.write(f"**Általános értékelés:** {exec_summary.get('altalanos_ertekeles', 'N/A')}")
    
    # 2. Bevételi elemzés
    st.subheader("💰 Bevételi statisztikák")
    col1, col2 = st.columns(2)
    col1.metric("Átlag havi bevétel", f"{eredmenyek['basic_stats']['user_income']/honapok:,.0f} Ft",
                f"hasonló profil átlag: {eredmenyek['basic_stats']['benchmark_income']/honapok:,.0f} Ft")
    col2.metric("Jövedelem rangsor", f"Top {eredmenyek['basic_stats']['user_rank_income']:.1f}%")
    
    # 3. Költség elemzés
    st.subheader("🧮 Kiadási elemzés")
    col1, col2 = st.columns(2)
    col1.metric("Átlag havi kiadás", f"{eredmenyek['basic_stats']['user_expenses']/honapok:,.0f} Ft")
    col2.metric("Tranzakciók száma (összes)", eredmenyek['transaction_count'])
    
    # Kiadási minták
    st.subheader("📊 Kiadási minták")
    col1, col2 = st.columns(2)
    col1.metric("Fix költségek havonta", f"{eredmenyek['spending_patterns']['fixed_costs']/honapok:,.0f} Ft", 
                   f"{eredmenyek['spending_patterns']['fixed_ratio']:.1f}%")
    col2.metric("Változó költségek havonta", f"{eredmenyek['spending_patterns']['variable_costs']/honapok:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['variable_ratio']:.1f}%")
    col3, col4 = st.columns(2)
    col3.metric("Fix költségeid aránya", f"{ml_insight['fix_cost']['fix_user']:.1%}",
                  f"hasonló profil átlag: {ml_insight['fix_cost']['fix_benchmark']:.1%}")
    
    col4.metric("Impulzusvásárlások", f"{eredmenyek['spending_patterns']['user_impulse_pct']:.1f}%",
                   f"profil átlag: {eredmenyek['spending_patterns']['profile_impulse_pct']:.1f}%")
    
    # Kategória elemzés
    st.subheader("🏷️ Kategória elemzés")
    top_cats = eredmenyek['category_analysis']['top_category']
    for rank in sorted(top_cats.keys()):
        cat = top_cats[rank]
        st.progress(cat['percentage']/100, 
                    text=f"{rank}. {cat['name']}: {cat['amount']:,.0f} Ft ({cat['percentage']:.1f}%)")
    
    if eredmenyek['category_analysis']['missing_essentials']:
        st.warning("Hiányzó alapkategóriák: " + ", ".join(eredmenyek['category_analysis']['missing_essentials']))
    
    # Időbeli minták
    st.subheader("⏰ Időbeli minták")
    week_data = eredmenyek['temporal_analysis']['weekly_spending']
    nap_rend = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    rendezett_heti_adat = {nap: week_data.get(nap, 0) for nap in nap_rend}
    st.bar_chart(pd.DataFrame.from_dict(rendezett_heti_adat, orient='index', columns=['Kiadás']))
    cols = st.columns(2)
    cols[0].metric("Legtöbb kiadás", f"{eredmenyek['temporal_analysis']['max_day']['name']}",
                   f"{eredmenyek['temporal_analysis']['max_day']['amount']:,.0f} Ft")
    cols[1].metric("Legkevesebb kiadás", f"{eredmenyek['temporal_analysis']['min_day']['name']}",
                   f"{eredmenyek['temporal_analysis']['min_day']['amount']:,.0f} Ft")
    
    # 4. Megtakarítási elemzés
    st.subheader("💵 Megtakarítási statisztikák")
    col1, col2 = st.columns(2)
    col1.metric("Megtakarítási ráta", f"{eredmenyek['basic_stats']['user_savings_rate']:.1f}%", 
                f"hasonló profil átlag: {eredmenyek['basic_stats']['benchmark_savings_rate']:.1f}%")
    col2.metric("Megtakarítás rangsor", f"Top {eredmenyek['basic_stats']['user_rank_savings']:.1f}%")
    
    # 5. Cashflow elemzés
    st.subheader("💸 Cashflow elemzés")
    st.line_chart(pd.DataFrame.from_dict(eredmenyek['cashflow']['monthly_flow'], orient='index', columns=['Havi nettó']))
    st.write(f"**Trend:** {eredmenyek['cashflow']['trend_msg']}")
    
    # Cash Flow Elemzés részletek
    st.subheader("📉 Cash Flow Elemzés részletek")
    cash_flow = jelentés["cash_flow_elemzes"]
    st.write(f"**Havi átlagos szükséglet kiadások:** {cash_flow['burn_rate'].get('havi_atlag_szukseglet', 'N/A'):,.0f} Ft")
    st.write(f"**Havi átlagos luxus kiadások:** {cash_flow['burn_rate'].get('havi_atlag_luxus', 'N/A'):,.0f} Ft")
    st.write(f"**Teljes havi átlagos kiadások:** {cash_flow['burn_rate'].get('total_burn_rate', 'N/A'):,.0f} Ft")
    
    st.write("**Mennyi ideig élnél meg a jelenlegi vagyonoddal?**")
    runway = cash_flow['runway'].get('runway_honapok', {})
    st.write(f"- Csak készpénz: {runway.get('csak_keszpenz', 'N/A')} hónap")
    st.write(f"- Összes asset: {runway.get('osszes_asset', 'N/A')} hónap")
    st.warning("Ajánlott tartalék: 3-6 hónap")
    
    # 6. Spórolási lehetőségek
    st.subheader("💡 Spórolási Optimalizáció")
    sporolas = jelentés["sporolas_optimalizacio"]
    
    if 'pareto_analysis' in sporolas:
        st.write("**Pareto elemzés (80/20 szabály):**")
        kat_darab = len(sporolas['pareto_analysis'].get('pareto_kategoriak', []))
        st.write(f"A kiadások {sporolas['pareto_analysis'].get('pareto_arany_pct', 'N/A')}%-a {kat_darab} kategóriából származik")
        for kat in sporolas['pareto_analysis'].get('pareto_kategoriak', [])[:kat_darab]:
            st.write(f"- {kat}")
    
    # 7. Befektetési tanácsok
    st.subheader("📈 Befektetési Tanácsok")
    befektetes = jelentés["befektetesi_elemzes"]
    
    if 'portfolio_suggestions' in befektetes:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Jelenlegi portfólió allokáció:**")
            for asset, pct in befektetes['portfolio_suggestions'].get('jelenlegi_allokaciok', {}).items():
                st.write(f"- {asset}: {pct:.0f}%")
        
        with col2:
            st.write("**Javasolt portfólió allokáció:**")
            for asset, pct in befektetes['portfolio_suggestions'].get('javasolt_allokaciok', {}).items():
                st.write(f"- {asset}: {pct:.0f}%")
        
        st.write("**Eladási és vételi javaslatok:**")
        for action in befektetes['portfolio_suggestions'].get('rebalancing_actions', []):
            st.write(f"- {action}")
    
    # 8. ML Insight elemzés            
    st.subheader("🤖 Gépi tanulás alapú elemzések")
    
    st.subheader("Kockázatelemzés")
    if "nem kerülsz mínuszba" in ml_insight['risk_msg']:
        st.success(ml_insight['risk_msg'])
    else:
        st.warning(ml_insight['risk_msg'])
    
    st.subheader("Mozgóátlagok")
    col1, col2, col3 = st.columns(3)
    col1.metric("7 napos átlagköltés", f"{abs(ml_insight['rolling_avg']['roll7']):,.0f} Ft")
    col2.metric("30 napos átlagköltés", f"{abs(ml_insight['rolling_avg']['roll30']):,.0f} Ft")
    col3.metric("90 napos átlagköltés", f"{abs(ml_insight['rolling_avg']['roll90']):,.0f} Ft")
    
    st.subheader("Költési diverzitás")
    st.metric("Diverzitási indexed", f"{ml_insight['diversity']['div_user']:.4f}",
              f"hasonló profil átlag: {ml_insight['diversity']['div_benchmark']:.4f}")
    
    st.subheader("Trendek")
    st.metric("Megtakarítás változása", f"{ml_insight['savings_trend_pp']:.1%}pont")
    
    st.metric("Ilyen helyzetben átlagosan elérhető vagyon", f"{ml_insight['suggested_assets']:,.0f} Ft")
    
    # 9. Ajánlások
    st.subheader("💡 Javaslatok")
    for rec in eredmenyek['recommendations']:
        st.write(f"- {rec}")
else:
    st.warning("Nincs elég adat az elemzéshez. Kérjük, adj hozzá új tranzakciókat.")