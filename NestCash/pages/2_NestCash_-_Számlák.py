# pages/2_💼_Számlák.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import plotly.express as px
from app import get_user_accounts, update_account_balance, save_data

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

st.title("💼 Számlák kezelése")

# Account management
tab1, tab2, tab3, tab4 = st.tabs(["Alszámlák", 
                                  "Pénzmozgatás számlák közt", 
                                  "Új alszámla létrehozása",
                                  "Célok kezelése"])

with tab1:
    user_accounts = get_user_accounts(current_user)
    st.write("### Alszámlák és egyenlegek")
    
    # Pie chart for each main account
    for foszamla, alszamlak in user_accounts.items():
        if alszamlak:  # Only show if there are sub-accounts
            # Prepare data for pie chart
            labels = list(alszamlak.keys())
            values = list(alszamlak.values())
            
            # Create pie chart
            fig = px.pie(
                names=labels,
                values=values,
                title=f"{foszamla.capitalize()} számla megoszlása",
                hover_data=[values],
                labels={'names': 'Alszámla', 'values': 'Egyenleg (Ft)'}
            )
            
            # Display the pie chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Optional: Display the raw numbers in an expander
            with st.expander(f"Részletes egyenlegek ({foszamla})"):
                for alszamla, egyenleg in alszamlak.items():
                    st.write(f"- {alszamla}: {egyenleg:,.0f} Ft")

with tab2:
    with st.form("szamlak_kozott"):
        col1, col2 = st.columns(2)
        
        with col1:
            forras_foszamla = st.selectbox("Forrás főszámla", ["likvid", "befektetes", "megtakaritas"])
            user_accounts = get_user_accounts(current_user)
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
                

# Módosítsd a célokat kezelő függvényeket:
def load_goals():
    try:
        return pd.read_csv("datafiles/user_goals.csv")
    except:
        return pd.DataFrame(columns=["goal_id", "user_id", "title", "target_amount", 
                                   "current_amount", "target_date", "category", 
                                   "priority", "status", "created_at"])

def save_goals(goals_df):
    goals_df.to_csv("datafiles/user_goals.csv", index=False)
    
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
                progress = min(goal['current_amount'] / goal['target_amount'], 1.0)
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