# pages/1_📝_Tranzakciók.py
import streamlit as st
import pandas as pd
from datetime import datetime
from app import get_user_accounts, update_account_balance, save_data

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

# A fájl elejére, az importok után adjuk hozzá:
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

st.title("📝 Tranzakciók kezelése")

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
                "assets": 0
            }
            
            new_balance = update_account_balance(current_user, foszamla, alszamla, new_row["osszeg"])
            
            user_accounts = get_user_accounts(current_user)
            likvid_osszeg = sum(user_accounts["likvid"].values())
            befektetes_osszeg = sum(user_accounts["befektetes"].values())
            megtakaritas_osszeg = sum(user_accounts["megtakaritas"].values())
            
            new_row["likvid"] = likvid_osszeg
            new_row["befektetes"] = befektetes_osszeg
            new_row["megtakaritas"] = megtakaritas_osszeg
            new_row["foszamla"] = foszamla
            new_row["alszamla"] = alszamla
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.df = df
            save_data(df)
            
            st.success("Tranzakció sikeresen hozzáadva!")
            st.rerun()

# View transactions
with st.expander("Nyers tranzakciók listája"):
    if not user_df.empty:
        st.dataframe(user_df.sort_values("datum", ascending=False))
    else:
        st.warning("Nincsenek tranzakciók ehhez a felhasználóhoz.")
        
if not user_df.empty:
    # Tranzakció szerkesztése/törlése
    st.subheader("Tranzakció módosítása")
    selected_transaction = st.selectbox(
        "Válassz tranzakciót", 
        user_df.sort_values("datum", ascending=False)["tranzakcio_id"].unique(),
        key="transaction_select"
    )
    
    if selected_transaction:
        transaction_data = user_df[user_df["tranzakcio_id"] == selected_transaction].iloc[0]
        
        tab_edit, tab_delete = st.tabs(["Szerkesztés", "Törlés"])
        
        with tab_edit:
            with st.form("edit_transaction_form"):
                st.write(f"Tranzakció szerkesztése: {selected_transaction}")
                
                # Mezők előzetes kitöltése a jelenlegi értékekkel
                new_amount = st.number_input("Összeg (Ft)", value=abs(transaction_data["osszeg"]))
                new_category = st.selectbox("Kategória", CATEGORIES, 
                          index=CATEGORIES.index(transaction_data["kategoria"]))
                new_type = st.selectbox("Típus", TYPES,
                      index=TYPES.index(transaction_data["tipus"]))
                new_description = st.text_input("Leírás", value=transaction_data["leiras"])
                
                submitted = st.form_submit_button("Módosítások mentése")
                
                if submitted:
                    # Ellenőrizzük, hogy a felhasználó biztos benne
                    confirm = st.checkbox("Biztosan módosítani szeretnéd ezt a tranzakciót?")
                    if confirm:
                        updated_data = {
                            "osszeg": new_amount if transaction_data["bev_kiad_tipus"] == "bevetel" else -new_amount,
                            "kategoria": new_category,
                            "tipus": new_type,
                            "leiras": new_description
                        }
                        
                        if update_transaction(selected_transaction, updated_data):
                            st.success("Tranzakció sikeresen frissítve!")
                            st.rerun()
                        else:
                            st.error("Hiba történt a tranzakció frissítése közben!")
        
        with tab_delete:
            st.warning("VIGYÁZAT: A tranzakció törlése nem vonható vissza!")
            with st.form("delete_transaction_form"):
                st.write(f"Törlésre kijelölve: {selected_transaction}")
                st.write(f"Összeg: {transaction_data['osszeg']} Ft")
                st.write(f"Kategória: {transaction_data['kategoria']}")
                
                confirm_delete = st.checkbox("Biztosan törölni szeretnéd ezt a tranzakciót?")
                submitted_delete = st.form_submit_button("Tranzakció törlése")
                
                if submitted_delete and confirm_delete:
                    if delete_transaction(selected_transaction):
                        st.success("Tranzakció sikeresen törölve!")
                        st.rerun()
                    else:
                        st.error("Hiba történt a tranzakció törlése közben!")
else:
    st.warning("Nincsenek tranzakciók ehhez a felhasználóhoz.")