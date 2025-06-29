import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from PenzugyiElemzo import PenzugyiElemzo
from UserFinancialEDA import UserFinancialEDA, run_user_eda
from MLinsight import MLinsight

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
    
    balance = user_df['balance'].iloc[-1]
    reszvenyek = user_df['reszvenyek'].iloc[-1]
    egyeb_befektetes = user_df['egyeb_befektetes'].iloc[-1]
    
    cols = st.columns(3)
    cols[0].metric("Készpénz", f"{balance:,.0f}Ft")
    cols[1].metric("Részvények", f"{reszvenyek:,.0f}Ft")
    cols[2].metric("Egyéb befektetés", f"{egyeb_befektetes:,.0f}Ft")
    
    # Számlák közti pénzmozgatás
    with st.expander(f"Pénz mozgatása számlák között (Felhasználó {current_user})"):
        with st.form("szamlak_kozott"):
            col1, col2 = st.columns(2)
            forras = col1.selectbox("Forrás számla", ["balance", "reszvenyek", "egyeb_befektetes"])
            cel = col2.selectbox("Cél számla", ["balance", "reszvenyek", "egyeb_befektetes"])
            osszeg = st.number_input("Összeg (Ft)", min_value=0, value=0)
            datum = st.date_input("Dátum", datetime.today())
            
            submitted = st.form_submit_button("Átutalás")
            
            if submitted and forras != cel:
                # Forrás számla csökkentése
                new_row = {
                    "datum": datum.strftime("%Y-%m-%d"),
                    "honap": datum.strftime("%Y-%m"),
                    "het": datum.isocalendar()[1],
                    "nap_sorszam": datum.weekday(),
                    "tranzakcio_id": f"{current_user}_{datum.strftime('%Y%m%d')}_{int(time.time())}_from",
                    "osszeg": 0,
                    "kategoria": "szamlak_kozott",
                    "user_id": current_user,
                    "profil": profil,
                    "tipus": "megtakaritas",
                    "leiras": f"{osszeg}Ft ({forras} → {cel})",
                    "forras": "internal_transfer",
                    "ismetlodo": False,
                    "fix_koltseg": False,
                    "bev_kiad_tipus": "szukseglet",
                    "platform": "utalas",
                    "helyszin": "Egyéb",
                    "deviza": "HUF",
                    "cimke": "",
                    "celhoz_kotott": False,
                    forras: user_df[forras].iloc[-1] - osszeg,
                    cel: user_df[cel].iloc[-1] + osszeg,
                    "assets": user_df["assets"].iloc[-1]  # assets nem változik
                }
                
                last_row = user_df.iloc[-1]
                # többi számla egyenlege változatlan
                for col in user_df.columns:
                    if col not in new_row.keys():
                        new_row[col] = last_row[col]
                
                # Mindkét sor hozzáadása
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("Pénzmozgatás sikeresen rögzítve!")
                st.rerun()

            elif submitted and forras == cel:
                st.error("A forrás és cél számla nem lehet ugyanaz!")
    
    # Új adat bevitele - CSAK A KIVÁLASZTOTT FELHASZNÁLÓHOZ
    with st.expander(f"➕ Új tranzakció hozzáadása (Felhasználó {current_user})"):
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
                    "tranzakcio_id": f"{current_user}_{datum.strftime('%Y%m%d')}_{int(time.time())}",
                    "osszeg": osszeg if bev_kiad_tipus == "bevetel" else -abs(osszeg),
                    "kategoria": kategoria,
                    "user_id": current_user,
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
                    "assets": 0
                }
                
                # Balance számítás - CSAK AZ ADOTT FELHASZNÁLÓ ADATAIBAN
                if not user_df.empty:
                    last_row = user_df.iloc[-1]
                    new_row["balance"] = last_row["balance"] + new_row["osszeg"]
                    new_row["assets"] = last_row["assets"] + new_row["osszeg"]
                    new_row["reszvenyek"] = last_row["reszvenyek"]
                    new_row["egyeb_befektetes"] = last_row["egyeb_befektetes"]
                else:
                    new_row["balance"] = new_row["osszeg"]
                    new_row["assets"] = new_row["osszeg"]
                    new_row["reszvenyek"] = 0
                    new_row["egyeb_befektetes"] = 0
                
                # Új sor hozzáadása az eredeti DF-hez
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                
                # Session state frissítése és újratöltés
                st.success("Tranzakció sikeresen hozzáadva!")
                st.rerun()

    # Adatok megtekintése - CSAK A KIVÁLASZTOTT FELHASZNÁLÓ ADATAI
    if st.checkbox(f"Nyers adatok megtekintése (Felhasználó {current_user})"):
        current_user_df = df[df["user_id"] == current_user]
        if not current_user_df.empty:
            st.dataframe(current_user_df)
        else:
            st.warning("Nincsenek tranzakciók ehhez a felhasználóhoz.")

    # Elemzés szekció - CSAK A KIVÁLASZTOTT FELHASZNÁLÓRA
    st.header(f"Pénzügyek Elemzése (Felhasználó {current_user})")
    
    if not df.empty and not user_df.empty:
        eredmenyek = run_user_eda(df, current_user)
        elemzo = PenzugyiElemzo(df)
        jelentés = elemzo.generate_comprehensive_report(current_user)
        ml_insight = MLinsight(df, current_user)
        
        honapok = len(user_df.honap.unique())
        with st.expander("Pénzügyek elemzése"):
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