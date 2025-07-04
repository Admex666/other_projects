# pages/1_📝_Tranzakciók.py - Javított verzió
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from database import load_data, get_user_accounts, update_account_balance, save_data, update_transaction, delete_transaction, db, check_automatic_habits

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

CATEGORIES = [
    'fizetes', 'elelmiszer', 'lakber', 'kozlekedes', 'snack', 
    'etterem', 'mozi', 'kave', 'rezsi', 'megtakaritas', 
    'apro vasarlas', 'kutyu', 'utazas', 'ruha', 'online rendeles',
    'reszveny_hozam', 'egyeb_hozam', 'szórakozás'
]

TYPES = [
    'bevetel', 'alap', 'impulzus', 'vagy', 
    'megtakaritas', 'befektetes_hozam'
]

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
st.header("📝 Tranzakciók kezelése")

# New transaction form
with st.expander("➕ Új tranzakció hozzáadása"):
    with st.form("uj_tranzakcio"):
        col1, col2 = st.columns(2)
        datum = col1.date_input("Dátum", datetime.today())
        osszeg = col2.number_input("Összeg (Ft)", value=0)
        
        col3, col4 = st.columns(2)
        kategoria = col3.selectbox("Kategória", CATEGORIES)
        tipus = col4.selectbox("Típus", TYPES)
        
        bev_kiad_tipus = st.selectbox("Bevétel/Kiadás típus", [
            "bevetel", "szukseglet", "luxus"
        ])
        
        foszamla = st.selectbox("Főszámla", ["likvid", "befektetes", "megtakaritas"])
        user_accounts = get_user_accounts(current_user)
        alszamlak = list(user_accounts.get(foszamla, {}).keys())
        
        if not alszamlak:
            st.warning(f"Nincs alszámla a {foszamla} főszámlához. Kérjük, hozzon létre egyet a Számlák oldalon!")
            alszamla = st.selectbox("Alszámla", ["foosszeg"])  # Alapértelmezett
        else:
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
                "profil": st.session_state.get('profil', 'alap'),
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
                "befektetes": 0,
                "megtakaritas": 0,
                "assets": 0,
                "foszamla": foszamla,
                "alszamla": alszamla,
                "ho": datum.strftime("%Y-%m")  # String formátumban
            }
            
            # Egyenleg frissítése
            update_account_balance(current_user, foszamla, alszamla, new_row["osszeg"])
            
            # Aktuális egyenlegek lekérése
            user_accounts = get_user_accounts(current_user)
            new_row["likvid"] = sum(user_accounts.get("likvid", {}).values())
            new_row["befektetes"] = sum(user_accounts.get("befektetes", {}).values())
            new_row["megtakaritas"] = sum(user_accounts.get("megtakaritas", {}).values())
            new_row["assets"] = new_row["likvid"] + new_row["befektetes"] + new_row["megtakaritas"]
            
            # DataFrame frissítése
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.df = df
            save_data(df)
            
            check_automatic_habits(current_user, new_row)
            
            st.success("Tranzakció sikeresen hozzáadva!")
            st.rerun()

# Tranzakciók listázása és módosítása
if not user_df.empty:
    with st.expander("Tranzakciók módosítása"):
    
        # Tranzakciók listázása dropdown-ban
        transaction_options = []
        for _, row in user_df.sort_values("datum", ascending=False).iterrows():
            display_text = f"{row['datum']} - {row['kategoria']} - {row['osszeg']}Ft - {row['leiras'][:30]}..."
            transaction_options.append((row['tranzakcio_id'], display_text))
        
        selected_transaction_id = st.selectbox(
            "Válassz tranzakciót módosításra",
            options=[t[0] for t in transaction_options],
            format_func=lambda x: next(t[1] for t in transaction_options if t[0] == x),
            key="transaction_select"
        )
        
        if selected_transaction_id:
            # Tranzakció adatainak lekérése MongoDB-ből
            transaction_data = db.transactions.find_one({"tranzakcio_id": selected_transaction_id})
            
            if transaction_data:
                selected_transaction_obj_id = transaction_data["_id"]
                tab_edit, tab_delete = st.tabs(["Szerkesztés", "Törlés"])
                
                with tab_edit:
                    with st.form("edit_transaction_form"):
                        st.write(f"**Tranzakció szerkesztése:** {selected_transaction_id}")
                        
                        # Mezők előzetes kitöltése
                        new_amount = st.number_input(
                            "Összeg (Ft)", 
                            value=abs(float(transaction_data.get("osszeg", 0)))
                        )
                        
                        # Kategória kiválasztása
                        try:
                            cat_index = CATEGORIES.index(transaction_data.get("kategoria", ""))
                        except ValueError:
                            cat_index = 0
                        new_category = st.selectbox("Kategória", CATEGORIES, index=cat_index)
                        
                        # Típus kiválasztása
                        try:
                            type_index = TYPES.index(transaction_data.get("tipus", ""))
                        except ValueError:
                            type_index = 0
                        new_type = st.selectbox("Típus", TYPES, index=type_index)
                        
                        new_description = st.text_input(
                            "Leírás", 
                            value=transaction_data.get("leiras", "")
                        )
                        
                        submitted = st.form_submit_button("Módosítások mentése")
                        
                        if submitted:
                            # Meghatározzuk az előjelet
                            is_income = transaction_data.get("bev_kiad_tipus") == "bevetel"
                            final_amount = float(new_amount) if is_income else -float(new_amount)
                            
                            updated_data = {
                                "osszeg": final_amount,
                                "kategoria": new_category,
                                "tipus": new_type,
                                "leiras": new_description
                            }
                            
                            if update_transaction(selected_transaction_obj_id, updated_data):
                                st.success("Tranzakció sikeresen frissítve!")
                                
                                # Session state frissítése
                                st.session_state.df = load_data()
                                st.rerun()
                            else:
                                st.error("Hiba történt a tranzakció frissítése közben!")
                
                with tab_delete:
                    st.warning("⚠️ **VIGYÁZAT:** A tranzakció törlése nem vonható vissza!")
                    
                    with st.form("delete_transaction_form"):
                        st.write(f"**Törlésre kijelölve:** {selected_transaction_id}")
                        st.write(f"**Összeg:** {transaction_data.get('osszeg', 0)} Ft")
                        st.write(f"**Kategória:** {transaction_data.get('kategoria', 'N/A')}")
                        st.write(f"**Leírás:** {transaction_data.get('leiras', 'N/A')}")
                        
                        confirm_delete = st.checkbox("Biztosan törölni szeretnéd ezt a tranzakciót?")
                        submitted_delete = st.form_submit_button("Tranzakció törlése")
                        
                        if submitted_delete and confirm_delete:
                            if delete_transaction(selected_transaction_id):
                                st.success("Tranzakció sikeresen törölve!")
                                
                                # Session state frissítése
                                st.session_state.df = load_data()
                                st.rerun()
                            else:
                                st.error("Hiba történt a tranzakció törlése közben!")
            else:
                st.error("A tranzakció nem található az adatbázisban!")

else:
    st.info("Nincsenek tranzakciók ehhez a felhasználóhoz.")

# Tranzakciók megjelenítése
with st.expander("📊 Tranzakciók listája"):
    if not user_df.empty:
        # Oszlopok rendezése és megjelenítése
        display_columns = [
            'datum', 'kategoria', 'osszeg', 'leiras', 'tipus', 
            'bev_kiad_tipus', 'foszamla', 'alszamla'
        ]
        
        display_df = user_df[display_columns].sort_values("datum", ascending=False)
        st.dataframe(display_df, use_container_width=True)
        
        # Összegzés
        st.subheader("📈 Összegzés")
        col1, col2, col3 = st.columns(3)
        
        total_income = user_df[user_df['bev_kiad_tipus'] == 'bevetel']['osszeg'].sum()
        total_expenses = abs(user_df[user_df['bev_kiad_tipus'] != 'bevetel']['osszeg'].sum())
        net_balance = total_income - total_expenses
        
        col1.metric("Összes bevétel", f"{total_income:,.0f} Ft")
        col2.metric("Összes kiadás", f"{total_expenses:,.0f} Ft")
        col3.metric("Nettó egyenleg", f"{net_balance:,.0f} Ft")
    else:
        st.info("Nincsenek tranzakciók ehhez a felhasználóhoz.")

# Frissítés a load_data importáláshoz
def load_data():
    """Tranzakciók újratöltése az adatbázisból"""
    from app import load_data as app_load_data
    return app_load_data()