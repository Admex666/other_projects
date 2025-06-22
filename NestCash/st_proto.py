import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from PenzugyiElemzo import PenzugyiElemzo

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
st.title("💰 Pénzügyi Elemző Alkalmazás")
st.subheader("Adatok bevitele és elemzés")

# Adatok betöltése
df = load_data()

# Új adat bevitele
with st.expander("➕ Új tranzakció hozzáadása"):
    with st.form("uj_tranzakcio"):
        col1, col2 = st.columns(2)
        datum = col1.date_input("Dátum", datetime.today())
        osszeg = col2.number_input("Összeg (Ft)", value=0)
        
        col3, col4 = st.columns(2)
        kategoria = col3.selectbox("Kategória", [
            "fizetes", "elelmiszer", "lakber", "kozlekedes", 
            "szórakozás", "egészség", "snack", "egyéb"
        ])
        user_id = col4.number_input("User ID", min_value=1, value=1)
        
        col5, col6 = st.columns(2)
        profil = col5.selectbox("Profil", [
            "alacsony_jov", "kozeposztaly", "magas_jov", "arerzekeny"
        ])
        tipus = col6.selectbox("Típus", ["alap", "impulzus"])
        
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
                "tranzakcio_id": f"{user_id}_{datum.strftime('%Y%m%d')}_{int(time.time())}",
                "osszeg": osszeg if bev_kiad_tipus == "bevetel" else -abs(osszeg),
                "kategoria": kategoria,
                "user_id": user_id,
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
            
            # Balance számítás
            user_data = df[df["user_id"] == user_id]
            if not user_data.empty:
                last_row = user_data.iloc[-1]
                new_row["balance"] = last_row["balance"] + new_row["osszeg"]
                new_row["assets"] = last_row["assets"] + new_row["osszeg"]
            else:
                new_row["balance"] = new_row["osszeg"]
                new_row["assets"] = new_row["osszeg"]
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Tranzakció sikeresen hozzáadva!")

# Adatok megtekintése
if st.checkbox("Adatbázis megtekintése"):
    st.dataframe(df)

# Elemzés szekció
st.header("Pénzügyi Elemzés")

if len(df) > 0:
    user_id = st.selectbox("Válassz felhasználót", df["user_id"].unique())
    
    if st.button("Elemzés indítása", type="primary"):
        with st.spinner("Elemzés folyamatban..."):
            elemzo = PenzugyiElemzo(df)
            jelentés = elemzo.generate_comprehensive_report(user_id)
            
            # Eredmények megjelenítése
            st.success("Elemzés kész!")
            
            # Executive Summary
            st.subheader("📊 Executive Summary")
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