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
    'bevetel', 'kiadas'
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
        #tipus = col4.selectbox("Típus", TYPES)
        
        bev_kiad_tipus = col4.selectbox("Típus", options=[
            {"name": "Bevétel", "value": "bevetel"}, 
            {"name": "Kiadás (alapvető)", "value": "szukseglet"}, 
            {"name": "Kiadás (nem alapvető)", "value": "luxus"}
        ],
            format_func=lambda x: x["name"])["value"]
        
        user_accounts = get_user_accounts(current_user)
        szamla_lista = [f'{foszamla}/{alszamla}' for foszamla in user_accounts.keys() for alszamla in user_accounts[foszamla].keys()]
        
        szamla = st.selectbox("Számla", szamla_lista)
        
        foszamla, alszamla = szamla.split('/')
        
        leiras = st.text_input("Leírás")
        platform = st.selectbox("Platform", options=[
            {"name": "Utalás","value": "utalas"}, 
            {"name": "Készpénz", "value": "készpénz"}, 
            {"name": "Kártya", "value": "kártya"}
            ],
            format_func=lambda x: x['name'])["value"]
        
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
                "tipus": None,
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
            
            # Havi korlát ellenőrzés
            from database import get_user_monthly_limits, calculate_monthly_progress
            from datetime import datetime
            
            current_month = datetime.now().strftime("%Y-%m")
            limits = get_user_monthly_limits(current_user)
            
            if kategoria in limits:
                progress = calculate_monthly_progress(current_user, current_month)
                if kategoria in progress:
                    limit_data = progress[kategoria]
                    
                    if limit_data["limit_type"] == "maximum":
                        if limit_data["current_amount"] > limit_data["limit_amount"]:
                            st.warning(f"⚠️ Figyelem! Túllépte a {kategoria} kategória havi korlátját ({limit_data['limit_amount']:,.0f} Ft)!")
                        elif limit_data["current_amount"] > limit_data["limit_amount"] * 0.8:
                            st.info(f"ℹ️ Közel a havi korláthoz: {kategoria} ({limit_data['current_amount']:,.0f} / {limit_data['limit_amount']:,.0f} Ft)")
            
            st.success("Tranzakció sikeresen hozzáadva!")
            st.rerun()

# Tranzakciók listázása és módosítása
if not user_df.empty:
    with st.expander("🎯 Havi korlátok beállítása"):
        from database import get_user_monthly_limits, save_user_monthly_limits
        
        st.subheader("Kategóriánkénti havi korlátok")
        
        # Meglévő korlátok betöltése
        current_limits = get_user_monthly_limits(current_user)
        
        # Új korlát hozzáadása
        with st.form("new_limit_form"):
            st.write("**Új korlát hozzáadása**")
            col1, col2, col3 = st.columns(3)
            
            limit_category = col1.selectbox("Kategória", CATEGORIES, key="limit_category")
            limit_type = col2.selectbox("Típus", ["maximum", "minimum"], key="limit_type")
            limit_amount = col3.number_input("Összeg (Ft)", min_value=0, key="limit_amount")
            
            if st.form_submit_button("Korlát hozzáadása"):
                if limit_category not in current_limits:
                    current_limits[limit_category] = {}
                
                current_limits[limit_category] = {
                    "type": limit_type,
                    "amount": limit_amount
                }
                
                save_user_monthly_limits(current_user, current_limits)
                st.success(f"Korlát beállítva: {limit_category} - {limit_type} {limit_amount:,.0f} Ft")
                st.rerun()
        
        # Meglévő korlátok megjelenítése és szerkesztése
        if current_limits:
            st.write("**Jelenlegi korlátok:**")
            for category, limit_data in current_limits.items():
                col1, col2, col3, col4 = st.columns(4)
                
                col1.write(f"**{category}**")
                col2.write(f"{limit_data['type']}")
                col3.write(f"{limit_data['amount']:,.0f} Ft")
                
                if col4.button("Törlés", key=f"delete_{category}"):
                    del current_limits[category]
                    save_user_monthly_limits(current_user, current_limits)
                    st.success(f"Korlát törölve: {category}")
                    st.rerun()
        else:
            st.info("Nincsenek beállított korlátok. Adj hozzá újat!")
        
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