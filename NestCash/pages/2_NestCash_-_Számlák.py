# pages/2_💼_Számlák.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import plotly.express as px
from database import get_user_accounts, update_account_balance, save_data, load_accounts, save_accounts, get_collection, update_collection, db

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]
user_accounts = get_user_accounts(current_user)

st.title("💰 NestCash prototípus")
st.success(f"👤 Bejelentkezve mint: {st.session_state.username} (ID: {current_user})")
if user_df.empty:
    likvid = 0
    befektetes = 0
    megtakaritas = 0
    profil = 'alap'
else:
    likvid = user_df['likvid'].iloc[-1]
    befektetes = user_df['befektetes'].iloc[-1]
    megtakaritas = user_df['megtakaritas'].iloc[-1]
    profil = user_df['profil'].iloc[-1]

cols = st.columns(3)
cols[0].metric("💵 Likvid", f"{likvid:,.0f}Ft")
cols[1].metric("📈 Befektetések", f"{befektetes:,.0f}Ft")
cols[2].metric("🏦 Megtakarítások", f"{megtakaritas:,.0f}Ft")

st.header("")
st.header("💼 Számlák kezelése")

# Account management
tab1, tab2, tab3, tab4 = st.tabs(["Alszámlák", 
                                  "Pénzmozgatás számlák közt", 
                                  "Új alszámla létrehozása",
                                  "Célok kezelése"])

# A tab1 tartalmát cseréld le erre:
with tab1:
    st.write("### Alszámlák és egyenlegek - Teljes pénzügyi struktúra")
    
    # Összes adat előkészítése a sunburst chart-hoz
    sunburst_data = []
    
    for foszamla, alszamlak in user_accounts.items():
        if alszamlak:  # Csak ha vannak alszámlák
            # NEM adjuk hozzá külön a főszámlát, mert a parent mezőből automatikusan létrejön
            # Alszámlák hozzáadása
            for alszamla, egyenleg in alszamlak.items():
                sunburst_data.append({
                    'name': alszamla,
                    'parent': foszamla.capitalize(),  # Ez fogja létrehozni a főszámla szintet
                    'value': egyenleg,
                    'type': 'alszámla'
                })
    
    # Sunburst chart létrehozása
    if sunburst_data:
        df_sunburst = pd.DataFrame(sunburst_data)
        
        fig = px.sunburst(
            df_sunburst,
            path=['parent', 'name'],  # Hierarchia: főszámla -> alszámla
            values='value',
            color='parent',  # Most a főszámla szerint színezzük
            title='Teljes pénzügyi struktúra',
            hover_data={'value': ':.0f Ft'},
            width=800,
            height=800
        )
        
        # Formázás
        fig.update_traces(
            textinfo="label+percent parent+value",
            texttemplate="<b>%{label}</b><br>%{percentParent:.1%}<br>%{value:,.0f} Ft",
            hovertemplate="<b>%{label}</b><br>Összeg: %{value:,.0f} Ft<br>%{percentParent:.1%} of %{parent}"
        )
        
        fig.update_layout(
            margin=dict(t=50, l=0, r=0, b=0),
            uniformtext=dict(minsize=12, mode='hide'),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Részletes egyenlegek expanderben
        with st.expander("📊 Részletes egyenlegek"):
            for foszamla, alszamlak in user_accounts.items():
                if alszamlak:
                    st.write(f"#### {foszamla.capitalize()} (összesen: {sum(alszamlak.values()):,.0f} Ft)")
                    for alszamla, egyenleg in alszamlak.items():
                        st.write(f"- {alszamla}: {egyenleg:,.0f} Ft")
    else:
        st.info("Nincsenek alszámlák a megjelenítéshez. Hozz létre újat a 'Új alszámla létrehozása' fülön!")
with tab2:
    with st.form("szamlak_kozott"):
        col1, col2 = st.columns(2)
        
        with col1:
            forras_foszamla = st.selectbox("Forrás főszámla", ["likvid", "befektetes", "megtakaritas"])
            forras_alszamlak = list(user_accounts.get(forras_foszamla, {}).keys())
            forras_alszamla = st.selectbox("Forrás alszámla", forras_alszamlak)
        
        with col2:
            cel_foszamla = st.selectbox("Cél főszámla", ["likvid", "befektetes", "megtakaritas"])
            cel_alszamlak = list(user_accounts.get(cel_foszamla, {}).keys())
            cel_alszamla = st.selectbox("Cél alszámla", cel_alszamlak)
        
        osszeg = st.number_input("Összeg (Ft)", min_value=0, value=0)
        datum = st.date_input("Dátum", datetime.today())
        
        submitted = st.form_submit_button("Átutalás")
        
        if submitted:
            if forras_foszamla == cel_foszamla and forras_alszamla == cel_alszamla:
                st.error("A forrás és cél számla nem lehet ugyanaz!")
            else:
                update_account_balance(current_user, forras_foszamla, forras_alszamla, -osszeg)
                update_account_balance(current_user, cel_foszamla, cel_alszamla, osszeg)
                
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
                    "profil": st.session_state.get('profil', 'alap'),
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
                    "foszamla": forras_foszamla,
                    "alszamla": forras_alszamla,
                    "cel_foszamla": cel_foszamla,
                    "cel_alszamla": cel_alszamla,
                    "transfer_amount": osszeg,
                    "likvid": likvid_osszeg,
                    "befektetes": befektetes_osszeg,
                    "megtakaritas": megtakaritas_osszeg,
                    "assets": user_df["assets"].iloc[-1] if not user_df.empty else 0
                }
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.df = df
                save_data(df)
                st.success("Pénzmozgatás sikeresen rögzítve!")
                st.rerun()
                
with tab3:
    with st.form("uj_alszamla"):
        foszamla = st.selectbox("Főszámla", ["likvid", "befektetes", "megtakaritas"])
        alszamla_nev = st.text_input("Alszámla neve")
        
        if st.form_submit_button("Létrehozás"):
            if not alszamla_nev.strip():
                st.error("Kérjük, adja meg az alszámla nevét!")
            else:
                try:
                    # Frissített user_accounts lekérése
                    user_accounts = get_user_accounts(current_user)
                    
                    if foszamla not in user_accounts:
                        user_accounts[foszamla] = {}
                    
                    if alszamla_nev in user_accounts[foszamla]:
                        st.error("Ez az alszámla már létezik!")
                    else:
                        # Új alszámla hozzáadása
                        user_accounts[foszamla][alszamla_nev] = 0
                        
                        # Accounts frissítése az adatbázisban
                        accounts_data = db["accounts"].find_one()
                        user_id_str = str(current_user)
                        
                        if accounts_data is None:
                            # Ha nincs accounts dokumentum, létrehozzuk
                            db["accounts"].insert_one({user_id_str: user_accounts})
                        else:
                            # Frissítjük a meglévő adatokat
                            db["accounts"].update_one(
                                {"_id": accounts_data["_id"]},
                                {"$set": {user_id_str: user_accounts}}
                            )
                        
                        st.success(f"Alszámla létrehozva: {alszamla_nev} a {foszamla} alatt")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Hiba történt az alszámla létrehozásakor: {e}")
                    st.error(f"Részletes hiba: {str(e)}")
                

# Módosítsd a célokat kezelő függvényeket:
# Célok kezelése MongoDB-vel
def load_goals():
    goals = list(db.goals.find({"user_id": str(current_user)}))
    return pd.DataFrame(goals) if goals else pd.DataFrame(columns=[
        "goal_id", "user_id", "title", "target_amount", 
        "current_amount", "target_date", "category",
        "priority", "status", "created_at"
    ])

def save_goals(goals_df):
    # Töröljük a régi célokat
    db.goals.delete_many({"user_id": str(current_user)})
    
    if not goals_df.empty:
        # Új célok beszúrása
        db.goals.insert_many(goals_df.to_dict("records"))
    
with tab4:
    st.header("Célok kezelése")
    
    # Új cél létrehozása
    with st.expander("➕ Új cél hozzáadása"):
        with st.form("new_goal_form"):
            title = st.text_input("Cél neve*")
            target_amount = st.number_input("Cél összege (Ft)*", min_value=0)
            target_date = st.date_input("Cél dátuma*", min_value=datetime.today())
            category = st.selectbox("Kategória", ["Megtakarítás", "Befektetés", "Vásárlás", "Utazás", "Egyéb"])
            priority = st.select_slider("Prioritás", ["Alacsony", "Közepes", "Magas"])
            
            if st.form_submit_button("Cél mentése"):
                goals_df = load_goals()
                new_goal_id = goals_df["goal_id"].max() + 1 if not goals_df.empty else 1
                
                new_goal = {
                    "goal_id": new_goal_id,
                    "user_id": current_user,
                    "title": title,
                    "target_amount": target_amount,
                    "current_amount": 0,
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "category": category,
                    "priority": priority,
                    "status": "Aktív",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                
                goals_df = pd.concat([goals_df, pd.DataFrame([new_goal])], ignore_index=True)
                save_goals(goals_df)
                st.success("Cél sikeresen létrehozva!")
                st.rerun()
    
    # Célok megjelenítése és kezelése
    st.subheader("Aktív célok")
    goals_df = load_goals()
    user_goals = goals_df[goals_df["user_id"] == current_user]
    
    if user_goals.empty:
        st.info("Nincsenek célok. Adj hozzá újat!")
    else:
        for _, goal in user_goals.iterrows():
            with st.expander(f"{goal['title']} ({goal['status']})"):
                progress = min(int(goal['current_amount']) / 
                               int(goal['target_amount']), 1.0)
                st.progress(progress, text=f"Haladás: {goal['current_amount']:,}Ft / {goal['target_amount']:,}Ft ({progress*100:.1f}%)")
                
                cols = st.columns(3)
                cols[0].metric("Cél összeg", f"{goal['target_amount']:,}Ft")
                cols[1].metric("Eddig összegyűjtve", f"{goal['current_amount']:,}Ft")
                cols[2].metric("Határidő", goal['target_date'])
                
                with st.form(key=f"update_goal_{goal['goal_id']}"):
                    amount_to_add = st.number_input("Összeg hozzáadása", min_value=0, key=f"add_{goal['goal_id']}")
                    
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("Összeg hozzáadása"):
                        goals_df.loc[goals_df["goal_id"] == goal["goal_id"], "current_amount"] += amount_to_add
                        save_goals(goals_df)
                        st.success("Összeg frissítve!")
                        st.rerun()
                    
                    if col2.form_submit_button("Cél törlése", type="secondary"):
                        goals_df = goals_df[goals_df["goal_id"] != goal["goal_id"]]
                        save_goals(goals_df)
                        st.success("Cél törölve!")
                        st.rerun()