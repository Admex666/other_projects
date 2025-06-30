import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import hashlib
import os
import json
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
            "cimke", "celhoz_kotott", "likvid", "befektetes", 
            "megtakaritas", "assets"
        ])

def save_data(df):
    df.to_csv("szintetikus_tranzakciok.csv", index=False)

# Streamlit alkalmazás
st.title("💰 NestCash prototípus")

# Adatok betöltése
df = load_data()

#%% Registration, sign-in
# Adjuk hozzá az importokhoz
import hashlib
import os

# Felhasználók betöltése
def load_users():
    try:
        return pd.read_csv("users.csv")
    except:
        return pd.DataFrame(columns=["user_id", "username", "password", "email", "registration_date"])

# Felhasználó mentése
def save_users(users_df):
    users_df.to_csv("users.csv", index=False)

# Jelszó hash-elése
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Felhasználó authentikálása
def authenticate_user(username, password):
    users_df = load_users()
    hashed_pw = hash_password(password)
    user = users_df[(users_df["username"] == username) & (users_df["password"] == hashed_pw)]
    return user.iloc[0] if not user.empty else None

# Session state inicializálása
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_id = None
    st.session_state.username = None
 
# Felület
# Ha nincs bejelentkezve felhasználó
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Bejelentkezés", "Regisztráció"])
    
    with tab1:
        with st.form("Bejelentkezés"):
            username = st.text_input("Felhasználónév")
            password = st.text_input("Jelszó", type="password")
            submitted = st.form_submit_button("Bejelentkezés")
            
            if submitted:
                user = authenticate_user(username, password)
                if user is not None:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user
                    st.session_state.user_id = user["user_id"]
                    st.session_state.username = user["username"]
                    st.success("Sikeres bejelentkezés!")
                    st.rerun()
                else:
                    st.error("Hibás felhasználónév vagy jelszó!")
    
    with tab2:
        with st.form("Regisztráció"):
            new_username = st.text_input("Új felhasználónév")
            new_password = st.text_input("Új jelszó", type="password")
            confirm_password = st.text_input("Jelszó megerősítése", type="password")
            email = st.text_input("E-mail cím")
            submitted = st.form_submit_button("Regisztráció")
            
            if submitted:
                users_df = load_users()
                
                # Validációk
                if new_password != confirm_password:
                    st.error("A jelszavak nem egyeznek!")
                elif new_username in users_df["username"].values:
                    st.error("Ez a felhasználónév már foglalt!")
                else:
                    # Új user_id generálása
                    new_user_id = users_df["user_id"].max() + 1 if not users_df.empty else 1
                    
                    new_user = {
                        "user_id": new_user_id,
                        "username": new_username,
                        "password": hash_password(new_password),
                        "email": email,
                        "registration_date": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                    save_users(users_df)
                    
                    st.session_state.logged_in = True
                    st.session_state.current_user = new_user
                    st.session_state.user_id = new_user_id
                    st.session_state.username = new_username
                    username = new_username
                    
                    st.success("Sikeres regisztráció! Automatikusan bejelentkeztél.")
                    st.rerun()
    
    st.stop()  # Ne jelenjen meg a tartalom, ha nincs bejelentkezve
    
# Ha be van jelentkezve, jelenítsük meg a kijelentkezés gombot
if st.session_state.logged_in:
    current_user = st.session_state.user_id
    username = st.session_state.username
    st.success(f"Bejelentkezve mint: {username} (ID: {current_user})")
    
    # Kijelentkezés gomb
    if st.button("Kijelentkezés", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.success("Sikeresen kijelentkeztél!")
        st.rerun()

    #%% Az aktuális felhasználó adatainak kinyerése
    st.subheader("Tranzakciók bevitele, számlák kezelése")
    
    user_df = df[df["user_id"] == current_user]
    
    if user_df.empty:
        likvid = 0
        befektetes = 0
        megtakaritas = 0
        profil = 'alap'  # Alapértelmezett profil
    else:
        likvid = user_df['likvid'].iloc[-1]
        befektetes = user_df['befektetes'].iloc[-1]
        megtakaritas = user_df['megtakaritas'].iloc[-1]
        profil = user_df['profil'].iloc[-1]
    
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
    
    cols = st.columns(3)
    cols[0].metric("Likvid", f"{likvid:,.0f}Ft")
    cols[1].metric("Befektetések", f"{befektetes:,.0f}Ft")
    cols[2].metric("Megtakarítások", f"{megtakaritas:,.0f}Ft")
    
    #%% Számlák közti pénzmozgatás, számlakezelés
    def load_accounts():
        try:
            with open("accounts.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_accounts(accounts_dict):
        with open("accounts.json", "w") as f:
            json.dump(accounts_dict, f)
    
    def get_user_accounts(user_id):
        accounts = load_accounts()
        user_id_str = str(user_id)
        
        if user_id_str not in accounts:
            # Alapértelmezett számlák létrehozása
            accounts[user_id_str] = {
                "likvid": {"foosszeg": 0},
                "befektetes": {"foosszeg": 0},
                "megtakaritas": {"foosszeg": 0}
            }
            save_accounts(accounts)
        
        return accounts[user_id_str]
    
    def update_account_balance(user_id, foszamla, alszamla, amount):
        accounts = load_accounts()
        user_id_str = str(user_id)
        
        if user_id_str not in accounts:
            accounts[user_id_str] = get_user_accounts(user_id)
        
        if foszamla not in accounts[user_id_str]:
            accounts[user_id_str][foszamla] = {}
        
        if alszamla not in accounts[user_id_str][foszamla]:
            accounts[user_id_str][foszamla][alszamla] = 0
        
        accounts[user_id_str][foszamla][alszamla] += amount
        save_accounts(accounts)
        return accounts[user_id_str][foszamla][alszamla]
    
    # Alszámlák kezelése (az egyenlegek megjelenítése után)
    with st.expander("💼 Számlák kezelése"):
        tab1, tab2, tab3 = st.tabs(["Alszámlák", "Alszámlák létrehozása", "Pénzmozgatás számlák közt"])
        
        with tab2:
            with st.form("uj_alszamla"):
                foszamla = st.selectbox("Főszámla", ["likvid", "befektetes", "megtakaritas"])
                alszamla_nev = st.text_input("Alszámla neve")
                
                if st.form_submit_button("Létrehozás"):
                    user_accounts = get_user_accounts(current_user)
                    
                    if foszamla not in user_accounts:
                        user_accounts[foszamla] = {}
                    
                    if alszamla_nev in user_accounts[foszamla]:
                        st.error("Ez az alszámla már létezik!")
                    else:
                        user_accounts[foszamla][alszamla_nev] = 0
                        accounts = load_accounts()
                        accounts[str(current_user)] = user_accounts
                        save_accounts(accounts)
                        st.success(f"Alszámla létrehozva: {alszamla_nev} a {foszamla} alatt")
                        st.rerun()
        
        with tab1:
            user_accounts = get_user_accounts(current_user)
            st.write("### Alszámlák és egyenlegek")
            
            for foszamla, alszamlak in user_accounts.items():
                st.write(f"**{foszamla.capitalize()}**")
                for alszamla, egyenleg in alszamlak.items():
                    st.write(f"- {alszamla}: {egyenleg:,.0f} Ft")
    
        # Számlák közti pénzmozgatás bővítése alszámlákkal
        with tab3:
            with st.form("szamlak_kozott"):
                col1, col2 = st.columns(2)
                
                # Forrás oldal
                with col1:
                    forras_foszamla = st.selectbox("Forrás főszámla", ["likvid", "befektetes", "megtakaritas"])
                    user_accounts = get_user_accounts(current_user)
                    forras_alszamlak = list(user_accounts.get(forras_foszamla, {}).keys())
                    forras_alszamla = st.selectbox("Forrás alszámla", forras_alszamlak)
                
                # Cél oldal
                with col2:
                    cel_foszamla = st.selectbox("Cél főszámla", ["likvid", "befektetes", "megtakaritas"])
                    cel_alszamlak = list(user_accounts.get(cel_foszamla, {}).keys())
                    cel_alszamla = st.selectbox("Cél alszámla", cel_alszamlak)
                
                osszeg = st.number_input("Összeg (Ft)", min_value=0, value=0)
                datum = st.date_input("Dátum", datetime.today())
                
                submitted = st.form_submit_button("Átutalás")
                
                if submitted:
                    # Ellenőrzés
                    if forras_foszamla == cel_foszamla and forras_alszamla == cel_alszamla:
                        st.error("A forrás és cél számla nem lehet ugyanaz!")
                    else:
                        # Forrás számla frissítése
                        update_account_balance(current_user, forras_foszamla, forras_alszamla, -osszeg)
                        # Cél számla frissítése
                        update_account_balance(current_user, cel_foszamla, cel_alszamla, osszeg)
                        
                        # Főszámlák frissítése
                        user_accounts = get_user_accounts(current_user)
                        likvid_osszeg = sum(user_accounts["likvid"].values())
                        befektetes_osszeg = sum(user_accounts["befektetes"].values())
                        megtakaritas_osszeg = sum(user_accounts["megtakaritas"].values())
                        
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
                            "leiras": f"{osszeg}Ft ({forras_alszamla} → {cel_alszamla})",
                            "forras": "internal_transfer",
                            "ismetlodo": False,
                            "fix_koltseg": False,
                            "bev_kiad_tipus": "szukseglet",
                            "platform": "utalas",
                            "helyszin": "Egyéb",
                            "deviza": "HUF",
                            "cimke": "",
                            "celhoz_kotott": False,
                            "likvid": likvid_osszeg,
                            "befektetes": befektetes_osszeg,
                            "megtakaritas": megtakaritas_osszeg,
                            "assets": user_df["assets"].iloc[-1]  # assets nem változik
                        }
                        
                        # Új sor hozzáadása
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success("Pénzmozgatás sikeresen rögzítve!")
                        st.rerun()
    
    #%% Új adat bevitele - CSAK A KIVÁLASZTOTT FELHASZNÁLÓHOZ
    with st.expander("➕ Új tranzakció hozzáadása"):
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
            
            # Számla kiválasztása
            foszamla = st.selectbox("Főszámla", ["likvid", "befektetes", "megtakaritas"])
            user_accounts = get_user_accounts(current_user)
            alszamlak = list(user_accounts.get(foszamla, {}).keys())
            alszamla = st.selectbox("Alszámla", alszamlak)
            
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
                    "likvid": 0,
                    "assets": 0
                }
                
                # Alszámla egyenleg frissítése
                new_balance = update_account_balance(current_user, foszamla, alszamla, new_row["osszeg"])
                
                # Főszámla egyenlegek újraszámolása
                user_accounts = get_user_accounts(current_user)
                likvid_osszeg = sum(user_accounts["likvid"].values())
                befektetes_osszeg = sum(user_accounts["befektetes"].values())
                megtakaritas_osszeg = sum(user_accounts["megtakaritas"].values())
                
                # Főszámla értékek beállítása
                new_row["likvid"] = likvid_osszeg
                new_row["befektetes"] = befektetes_osszeg
                new_row["megtakaritas"] = megtakaritas_osszeg
                new_row["foszamla"] = foszamla
                new_row["alszamla"] = alszamla
                
                """
                # likvid számítás - CSAK AZ ADOTT FELHASZNÁLÓ ADATAIBAN
                if not user_df.empty:
                    last_row = user_df.iloc[-1]
                    new_row["likvid"] = last_row["likvid"] + new_row["osszeg"]
                    new_row["assets"] = last_row["assets"] + new_row["osszeg"]
                    new_row["befektetes"] = last_row["befektetes"]
                    new_row["megtakaritas"] = last_row["megtakaritas"]
                else:
                    new_row["likvid"] = new_row["osszeg"]
                    new_row["assets"] = new_row["osszeg"]
                    new_row["befektetes"] = 0
                    new_row["megtakaritas"] = 0
                """
                # Új sor hozzáadása az eredeti DF-hez
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                
                # Session state frissítése és újratöltés
                st.success("Tranzakció sikeresen hozzáadva!")
                st.rerun()

    # Adatok megtekintése - CSAK A KIVÁLASZTOTT FELHASZNÁLÓ ADATAI
    if st.checkbox(f"Nyers adatok megtekintése"):
        current_user_df = df[df["user_id"] == current_user]
        if not current_user_df.empty:
            st.dataframe(current_user_df)
        else:
            st.warning("Nincsenek tranzakciók ehhez a felhasználóhoz.")

    # Elemzés szekció - CSAK A KIVÁLASZTOTT FELHASZNÁLÓRA
    st.header(f"Pénzügyek Elemzése")
    
    if not (len(df) < 20) and not (len(user_df) < 20):
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
