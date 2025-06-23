import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from PenzugyiElemzo import PenzugyiElemzo
from UserFinancialEDA import UserFinancialEDA, run_user_eda

# Adatbázis kezelése
def load_data():
    try:
        return pd.read_csv("szintetikus_tranzakciok.csv")
    except:
        return pd.DataFrame(columns=[
            "datum", "honap", "het", "nap_sorszam", "tranzakcio_id", 
            "osszeg", "kategoria", "user_id", "profil", "tipus", 
            "leiras", "forras", "ismetlodo", "fix_koltseg", 
            "bev_kiad_tipus", "platform", "helyszin", "deviza", 
            "cimke", "celhoz_kotott", "balance", "reszvenyek", 
            "egyeb_befektetes", "assets"
        ])

def save_data(df):
    df.to_csv("szintetikus_tranzakciok.csv", index=False)

# Streamlit alkalmazás
st.title("💰 NestCash prototípus")
st.subheader("Tranzakciók bevitele és elemzés")

# Adatok betöltése
df = load_data()

# Session state inicializálása
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# User kiválasztása
if not df.empty:
    available_users = df["user_id"].unique().tolist()
else:
    available_users = []

# Ha nincs még felhasználó, lehetőség új létrehozására
if not available_users:
    st.info("Nincsenek még felhasználók az adatbázisban. Kérjük, hozzon létre egy új felhasználót.")
    new_user_id = st.number_input("Új felhasználó ID", min_value=1, value=1)
    if st.button("Felhasználó létrehozása"):
        st.session_state.selected_user = new_user_id
        st.success(f"Felhasználó {new_user_id} létrehozva! Most már hozzáadhat tranzakciókat.")
else:
    # User kiválasztása
    selected_user = st.selectbox(
        "Válaszd ki a felhasználódat", 
        available_users,
        index=available_users.index(st.session_state.selected_user) if st.session_state.selected_user else 0
    )
    
    # Session state frissítése
    if selected_user != st.session_state.selected_user:
        st.session_state.selected_user = selected_user
        st.rerun()
    
    st.success(f"Bejelentkezve mint: Felhasználó {st.session_state.selected_user}")

# Csak akkor folytatjuk, ha van kiválasztott felhasználó
if st.session_state.selected_user is not None:
    current_user = st.session_state.selected_user
    # Az aktuális felhasználó adatainak kinyerése
    user_df = df[df["user_id"] == current_user]
    balance = user_df['balance'].iloc[-1]
    st.write(f"Készpénz: **{balance:,.0f}Ft**")
    reszvenyek = user_df['reszvenyek'].iloc[-1]
    st.write(f"Részvények: **{reszvenyek:,.0f}Ft**")
    egyeb_befektetes = user_df['egyeb_befektetes'].iloc[-1]
    st.write(f"Egyéb befektetés: **{egyeb_befektetes:,.0f}Ft**")
    
    
    # Új adat bevitele - CSAK A KIVÁLASZTOTT FELHASZNÁLÓHOZ
    with st.expander(f"➕ Új tranzakció hozzáadása (Felhasználó {st.session_state.selected_user})"):
        with st.form("uj_tranzakcio"):
            col1, col2 = st.columns(2)
            datum = col1.date_input("Dátum", datetime.today())
            osszeg = col2.number_input("Összeg (Ft)", value=0)
            
            col3, col4 = st.columns(2)
            kategoria = col3.selectbox("Kategória", ['fizetes', 'elelmiszer', 
                                        'lakber', 'kozlekedes', 'snack', 
                                        'etterem', 'mozi', 'kave', 'rezsi', 
                                        'megtakaritas', 'apro vasarlas', 'kutyu',
                                        'utazas', 'ruha', 'online rendeles',
                                        'reszveny_hozam', 'egyeb_hozam', 'szórakozás']
                                       )

            # Profil és típus
            col5, col6 = st.columns(2)
            profil = user_df['profil'].iloc[-1] if current_user in df.user_id.unique() else None
            
            if pd.isna(profil):
                ossz_fizu = user_df[user_df.kategoria == 'fizetes']['osszeg'].sum()
                honapok = len(user_df.honap.unique())
                atlag_fizu = ossz_fizu / honapok
                ossz_koltes = abs(user_df[user_df.osszeg < 0]['osszeg'].sum())
                koltes_arany = ossz_koltes / ossz_fizu
                
                profil = 'arerzekeny' if koltes_arany < 0.70 else 'alacsony_jov' if atlag_fizu < 270_000\
                    else 'kozeposztaly' if atlag_fizu < 500_000 else 'magas_jov'
                
            profile_df = df[df.profil == profil].copy()
            
            tipus = col5.selectbox("Típus", ['bevetel', 'alap', 'impulzus', 
                                             'vagy', 'megtakaritas', 'befektetes_hozam']
                                   )
            
            bev_kiad_tipus = st.selectbox("Bevétel/Kiadás típus", [
                "bevetel", "szukseglet", "luxus"
            ])
            
            leiras = st.text_input("Leírás")
            platform = st.selectbox("Platform", ["utalas", "készpénz", "kártya", "web"])
            
            submitted = st.form_submit_button("Hozzáadás")
            
            if submitted:
                new_row = {
                    "datum": datum.strftime("%Y-%m-%d"),
                    "honap": datum.strftime("%Y-%m"),
                    "het": datum.isocalendar()[1],
                    "nap_sorszam": datum.weekday(),
                    "tranzakcio_id": f"{st.session_state.selected_user}_{datum.strftime('%Y%m%d')}_{int(time.time())}",
                    "osszeg": osszeg if bev_kiad_tipus == "bevetel" else -abs(osszeg),
                    "kategoria": kategoria,
                    "user_id": st.session_state.selected_user,
                    "profil": profil,
                    "tipus": tipus,
                    "leiras": leiras,
                    "forras": "user",
                    "ismetlodo": False,
                    "fix_koltseg": kategoria in ["lakber", "rezsi"],
                    "bev_kiad_tipus": bev_kiad_tipus,
                    "platform": platform,
                    "helyszin": "Egyéb",
                    "deviza": "HUF",
                    "cimke": "",
                    "celhoz_kotott": False,
                    "balance": 0,
                    "reszvenyek": 0,
                    "egyeb_befektetes": 0,
                    "assets": 0
                }
                
                # Balance számítás - CSAK AZ ADOTT FELHASZNÁLÓ ADATAIBAN
                if not user_df.empty:
                    last_row = user_df.iloc[-1]
                    new_row["balance"] = last_row["balance"] + new_row["osszeg"]
                    new_row["assets"] = last_row["assets"] + new_row["osszeg"]
                else:
                    new_row["balance"] = new_row["osszeg"]
                    new_row["assets"] = new_row["osszeg"]
                
                # Új sor hozzáadása az eredeti DF-hez
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                
                # Session state frissítése és újratöltés
                st.success("Tranzakció sikeresen hozzáadva!")
                st.experimental_rerun()

    # Adatok megtekintése - CSAK A KIVÁLASZTOTT FELHASZNÁLÓ ADATAI
    if st.checkbox(f"Adatok megtekintése (Felhasználó {st.session_state.selected_user})"):
        current_user_df = df[df["user_id"] == current_user]
        if not current_user_df.empty:
            st.dataframe(current_user_df)
        else:
            st.warning("Nincsenek tranzakciók ehhez a felhasználóhoz.")

    # Elemzés szekció - CSAK A KIVÁLASZTOTT FELHASZNÁLÓRA
    st.header(f"Pénzügyi Elemzés - Felhasználó {st.session_state.selected_user}")
    
    if not df.empty and not user_df.empty:
        if st.button("Elemzés indítása", type="primary"):
            with st.spinner("Elemzés folyamatban..."):
                elemzo = PenzugyiElemzo(df)
                jelentés = elemzo.generate_comprehensive_report(st.session_state.selected_user)
                
                # Eredmények megjelenítése
                st.success("Elemzés kész!")
                
                # Executive Summary
                st.subheader("📊 Összefoglaló")
                exec_summary = jelentés["executive_summary"]
                st.write(f"**Pénzügyi egészség pontszám:** {exec_summary.get('penzugyi_egeszseg_pontszam', 'N/A')}")
                st.write(f"**Általános értékelés:** {exec_summary.get('altalanos_ertekeles', 'N/A')}")
                
                st.write("**Fő erősségek:**")
                for erosseg in exec_summary.get('fo_erosegek', []):
                    st.write(f"- {erosseg}")
                
                st.write("**Fő kihívások:**")
                for kihivas in exec_summary.get('fo_kihivasok', []):
                    st.write(f"- {kihivas}")
                
                st.write("**Legfontosabb ajánlások:**")
                for ajanlas in exec_summary.get('legfontosabb_ajanlasok', []):
                    st.write(f"- {ajanlas}")
                
                # Cash Flow Elemzés
                st.subheader("💸 Cash Flow Elemzés")
                cash_flow = jelentés["cash_flow_elemzes"]
                
                st.write(f"**Havi átlagos szükséglet kiadások:** {cash_flow['burn_rate'].get('havi_atlag_szukseglet', 'N/A'):,.0f} Ft")
                st.write(f"**Havi átlagos luxus kiadások:** {cash_flow['burn_rate'].get('havi_atlag_luxus', 'N/A'):,.0f} Ft")
                st.write(f"**Teljes burn rate:** {cash_flow['burn_rate'].get('total_burn_rate', 'N/A'):,.0f} Ft")
                
                st.write("**Runway elemzés:**")
                runway = cash_flow['runway'].get('runway_honapok', {})
                st.write(f"- Csak készpénz: {runway.get('csak_keszpenz', 'N/A')} hónap")
                st.write(f"- Összes asset: {runway.get('osszes_asset', 'N/A')} hónap")
                
                # Spórolási lehetőségek
                st.subheader("💡 Spórolási Optimalizáció")
                sporolas = jelentés["sporolas_optimalizacio"]
                
                if 'pareto_analysis' in sporolas:
                    st.write(f"**Pareto elemzés (80/20 szabály):**")
                    st.write(f"A kiadások {sporolas['pareto_analysis'].get('pareto_arany_pct', 'N/A')}%-a {len(sporolas['pareto_analysis'].get('pareto_kategoriak', []))} kategóriából származik")
                    st.write("Top kategóriák:")
                    for kat in sporolas['pareto_analysis'].get('pareto_kategoriak', [])[:3]:
                        st.write(f"- {kat}")
                
                # Befektetési tanácsok
                st.subheader("📈 Befektetési Tanácsok")
                befektetes = jelentés["befektetesi_elemzes"]
                
                if 'portfolio_suggestions' in befektetes:
                    st.write("**Jelenlegi portfólió allokáció:**")
                    for asset, pct in befektetes['portfolio_suggestions'].get('jelenlegi_allokaciok', {}).items():
                        st.write(f"- {asset}: {pct:.0f}%")
                    
                    st.write("**Javasolt portfólió allokáció:**")
                    for asset, pct in befektetes['portfolio_suggestions'].get('javasolt_allokaciok', {}).items():
                        st.write(f"- {asset}: {pct:.0f}%")
                    
                    st.write("**Rebalancing javaslatok:**")
                    for action in befektetes['portfolio_suggestions'].get('rebalancing_actions', []):
                        st.write(f"- {action}")
    else:
        st.warning("Nincs elég adat az elemzéshez. Kérjük, adj hozzá új tranzakciókat.")
     
    eredmenyek = run_user_eda(df, current_user)        
    # Elemzés eredményeinek megjelenítése
    st.header(f"Pénzügyi Elemzés - Felhasználó {eredmenyek['user_id']}")
    
    # Dashboard generálása
    dashboard_fig = UserFinancialEDA(df)._create_user_dashboard(
        user_data=user_df,
        profile_data=profile_df,
        user_profile=profil
    )
    
    # Dashboard megjelenítése
    st.subheader("📈 Pénzügyi Dashboard")
    st.pyplot(dashboard_fig)

    # 1. Alapadatok
    with st.expander("📌 Alapadatok"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Profil", eredmenyek['profile'])
        col2.metric("Időszak", f"{eredmenyek['time_period']['start']} - {eredmenyek['time_period']['end']}")
        col3.metric("Tranzakciók száma", eredmenyek['transaction_count'])
    
    # 2. Alap statisztikák
    st.subheader("📊 Alap statisztikák")
    cols = st.columns(4)
    cols[0].metric("Összes bevétel", f"{eredmenyek['basic_stats']['user_income']:,.0f} Ft")
    cols[1].metric("Összes kiadás", f"{eredmenyek['basic_stats']['user_expenses']:,.0f} Ft")
    cols[2].metric("Nettó", f"{eredmenyek['basic_stats']['user_net']:,.0f} Ft")
    cols[3].metric("Megtakarítási ráta", f"{eredmenyek['basic_stats']['user_savings_rate']:.1f}%")
    
    # Benchmark adatok
    with st.expander("Benchmark összehasonlítás"):
        st.write(f"**Hasonló profil átlag jövedelem:** {eredmenyek['basic_stats']['benchmark_income']:,.0f} Ft")
        st.write(f"**Hasonló profil átlag megtakarítási ráta:** {eredmenyek['basic_stats']['benchmark_savings_rate']:.1f}%")
        st.write(f"**Jövedelem rangsor:** Top {eredmenyek['basic_stats']['user_rank_income']}%")
        st.write(f"**Megtakarítás rangsor:** Top {eredmenyek['basic_stats']['user_rank_savings']}%")
    
    # 3. Cashflow elemzés
    st.subheader("💸 Cashflow elemzés")
    st.line_chart(pd.DataFrame.from_dict(eredmenyek['cashflow']['monthly_flow'], orient='index', columns=['Havi nettó']))
    st.write(f"**Trend:** {eredmenyek['cashflow']['trend_msg']}")
    
    # 4. Kiadási minták
    st.subheader("🧮 Kiadási minták")
    cols = st.columns(3)
    cols[0].metric("Fix költségek", f"{eredmenyek['spending_patterns']['fixed_costs']:,.0f} Ft", 
                   f"{eredmenyek['spending_patterns']['fixed_ratio']:.1f}%")
    cols[1].metric("Változó költségek", f"{eredmenyek['spending_patterns']['variable_costs']:,.0f} Ft",
                   f"{eredmenyek['spending_patterns']['variable_ratio']:.1f}%")
    cols[2].metric("Impulzusvásárlások", f"{eredmenyek['spending_patterns']['user_impulse_pct']:.1f}%",
                   f"profil átlag: {eredmenyek['spending_patterns']['profile_impulse_pct']:.1f}%")
    
    # 5. Kategória elemzés
    st.subheader("🏷️ Kategória elemzés")
    top_cats = eredmenyek['category_analysis']['top_category']
    for rank in sorted(top_cats.keys()):
        cat = top_cats[rank]
        st.progress(cat['percentage']/100, 
                    text=f"{rank}. {cat['name']}: {cat['amount']:,.0f} Ft ({cat['percentage']:.1f}%)")
    
    if eredmenyek['category_analysis']['missing_essentials']:
        st.warning("Hiányzó alapkategóriák: " + ", ".join(eredmenyek['category_analysis']['missing_essentials']))
    
    # 6. Időbeli elemzés
    st.subheader("⏰ Időbeli minták")
    week_data = eredmenyek['temporal_analysis']['weekly_spending']
    st.bar_chart(pd.DataFrame.from_dict(week_data, orient='index', columns=['Kiadás']))
    cols = st.columns(2)
    cols[0].metric("Legtöbb kiadás", f"{eredmenyek['temporal_analysis']['max_day']['name']}",
                   f"{eredmenyek['temporal_analysis']['max_day']['amount']:,.0f} Ft")
    cols[1].metric("Legkevesebb kiadás", f"{eredmenyek['temporal_analysis']['min_day']['name']}",
                   f"{eredmenyek['temporal_analysis']['min_day']['amount']:,.0f} Ft")
    
    # 7. Kockázatelemzés
    st.subheader("⚠️ Kockázatelemzés")
    risk = eredmenyek['risk_analysis']
    st.write(f"**Kockázati szint:** {risk['risk_level']}")
    st.write(risk['risk_msg'])
    st.write(f"Fix költségek/jövedelem arány: {risk['fixed_ratio']:.1f}%")
    
    # 8. Ajánlások
    st.subheader("💡 Javaslatok")
    for rec in eredmenyek['recommendations']:
        st.write(f"- {rec}")