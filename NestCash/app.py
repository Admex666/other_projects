# app.py - Main application file (javított verzió)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import hashlib
import os
import json
from pathlib import Path
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import streamlit as st

def get_mongo_client():
    try:
        client = MongoClient(
            st.secrets["mongo"]["uri"],
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=30000,  # 30 second connection timeout
            socketTimeoutMS=30000  # 30 second socket timeout
        )
        # Test the connection
        client.admin.command('ping')
        return client
    except ServerSelectionTimeoutError:
        st.error("⚠️ Could not connect to MongoDB: Timeout occurred")
        st.stop()
    except ConnectionFailure as e:
        st.error(f"⚠️ MongoDB connection failed: {e}")
        st.stop()

# Initialize connection
try:
    client = get_mongo_client()
    db = client.dbname  # Your database name
except Exception as e:
    st.error(f"⚠️ Critical error initializing database: {e}")
    st.stop()

# Temporary debug section
with st.expander("Connection Debug Info"):
    try:
        st.write("### MongoDB Connection Test")
        st.write("Server info:", client.server_info())
        st.write("Database stats:", db.command("dbstats"))
        st.write("Collections:", db.list_collection_names())
    except Exception as e:
        st.error(f"Debug failed: {e}")

#%% Common functions and session state management
def load_data():
    """Tranzakciók betöltése"""
    transactions = list(db["transactions"].find({}, {'_id': 0}))
    return pd.DataFrame(transactions) if transactions else pd.DataFrame()

def save_data(df):
    """Tranzakciók mentése - Period objektumok kezelésével"""
    if df.empty:
        return
    
    # Pandas Period objektumok átalakítása stringgé
    if 'ho' in df.columns:
        df['ho'] = df['ho'].astype(str)
    
    # NaN és inf értékek kezelése
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna('')
    
    # DataFrame konvertálása dictionary listává
    records = df.to_dict("records")
    
    # Összes problémás típus konvertálása
    for record in records:
        for key, value in record.items():
            # Period objektumok kezelése
            if hasattr(value, 'strftime'):
                record[key] = str(value)
            # NaN értékek kezelése
            elif pd.isna(value):
                record[key] = None
            # Numpy típusok kezelése
            elif isinstance(value, (np.integer, np.floating)):
                if pd.isna(value):
                    record[key] = None
                else:
                    record[key] = float(value) if isinstance(value, np.floating) else int(value)
    
    # Régi adatok törlése és újak beszúrása
    db["transactions"].delete_many({})
    if records:
        db["transactions"].insert_many(records)

def load_users():
    users = get_collection("users")
    if not users:
        return pd.DataFrame(columns=["user_id", "username", "password", "email", "registration_date"])
    return pd.DataFrame.from_dict(users, orient='index')

def save_users(users_df):
    users_dict = users_df.set_index(users_df['user_id'].astype(str)).to_dict(orient='index')
    update_collection("users", users_dict)

def get_collection(collection_name):
    """MongoDB kollekció lekérése dictionary-ként"""
    docs = list(db[collection_name].find({}))
    return {str(doc["_id"]): doc for doc in docs} if docs else {}

def update_collection(collection_name, data_dict):
    """MongoDB kollekció frissítése"""
    try:
        if collection_name == "accounts":
            # Az accounts speciális kezelése
            existing_accounts = db[collection_name].find_one()
            
            if existing_accounts is None:
                # Ha nincs accounts dokumentum, létrehozzuk
                db[collection_name].insert_one(data_dict)
            else:
                # Frissítjük a meglévő adatokat
                update_data = {k: v for k, v in data_dict.items() if k != "_id"}
                db[collection_name].update_one(
                    {"_id": existing_accounts["_id"]},
                    {"$set": update_data},
                    upsert=True
                )
        else:
            # Egyéb kollekciók kezelése
            for doc_id, data in data_dict.items():
                try:
                    # Csak akkor próbálunk ObjectId-t létrehozni, ha az doc_id valid formátumú
                    if len(doc_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in doc_id):
                        object_id = ObjectId(doc_id)
                    else:
                        # Ha nem valid ObjectId, akkor keressük más módon
                        existing_doc = db[collection_name].find_one({"user_id": doc_id})
                        if existing_doc:
                            object_id = existing_doc["_id"]
                        else:
                            # Ha nincs ilyen dokumentum, hozzunk létre újat
                            data["user_id"] = doc_id
                            result = db[collection_name].insert_one(data)
                            continue
                    
                    db[collection_name].update_one(
                        {"_id": object_id},
                        {"$set": data},
                        upsert=True
                    )
                except Exception as e:
                    st.error(f"Hiba a dokumentum frissítésekor: {e}")
                    continue
                    
    except Exception as e:
        st.error(f"Hiba történt a kollekció frissítésekor: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    user = db.users.find_one({"username": username})
    if user and user.get("password") == hash_password(password):
        st.session_state.user_id = user["user_id"]
        return user
    return None

def get_user_accounts(user_id):
    """Felhasználói számlák lekérése az accounts dokumentumból"""
    try:
        user_id_str = str(user_id)
        accounts_data = db["accounts"].find_one()
        
        if accounts_data and user_id_str in accounts_data:
            return accounts_data[user_id_str]
        
        # Alapértelmezett struktúra, ha nincs ilyen felhasználó
        default_accounts = {
            "likvid": {"foosszeg": 0},
            "befektetes": {"foosszeg": 0},
            "megtakaritas": {"foosszeg": 0}
        }
        
        # Hozzáadjuk az alapértelmezett struktúrát az adatbázishoz
        if accounts_data is None:
            db["accounts"].insert_one({user_id_str: default_accounts})
        else:
            db["accounts"].update_one(
                {"_id": accounts_data["_id"]},
                {"$set": {user_id_str: default_accounts}}
            )
        
        return default_accounts
        
    except Exception as e:
        st.error(f"Hiba történt a számlaadatok lekérésekor: {e}")
        return {
            "likvid": {"foosszeg": 0},
            "befektetes": {"foosszeg": 0},
            "megtakaritas": {"foosszeg": 0}
        }

def update_account_balance(user_id, foszamla, alszamla, amount):
    """Számlegyenleg frissítése"""
    try:
        user_id_str = str(user_id)
        
        accounts_data = db["accounts"].find_one()
        
        if not accounts_data:
            accounts_data = {}
        
        if user_id_str not in accounts_data:
            accounts_data[user_id_str] = {
                "likvid": {"foosszeg": 0},
                "befektetes": {"foosszeg": 0},
                "megtakaritas": {"foosszeg": 0}
            }

        db["accounts"].update_one(
            {"_id": accounts_data["_id"]} if "_id" in accounts_data else {},
            {"$inc": {f'{user_id_str}.{foszamla}.{alszamla}': amount}}
        )
        
        
        return db["accounts"].find_one()[user_id_str][foszamla][alszamla]
        
    except Exception as e:
        st.error(f"Hiba történt az egyenleg frissítésekor: {e}")
        return 0

def load_accounts():
    accounts = get_collection("accounts")
    return accounts if accounts else {}

def save_accounts(accounts_dict):
    """Speciális accounts mentési logika"""
    try:
        # Ellenőrizzük, hogy van-e adat
        if not accounts_dict:
            st.warning("Nincsenek mentendő számlaadatok")
            return False
        
        # Az accounts dokumentum teljes lekérése
        existing_accounts = db["accounts"].find_one()
        
        if existing_accounts is None:
            # Ha nincs accounts dokumentum, létrehozzuk
            db["accounts"].insert_one(accounts_dict)
        else:
            # Frissítjük a meglévő adatokat
            for user_id, user_data in accounts_dict.items():
                existing_accounts[user_id] = user_data
            
            # Mentjük vissza az adatbázisba
            db["accounts"].update_one(
                {"_id": existing_accounts["_id"]},
                {"$set": {k: v for k, v in existing_accounts.items() if k != "_id"}},
                upsert=True
            )
        
        return True
        
    except Exception as e:
        st.error(f"Hiba történt az accounts mentésekor: {e}")
        return False

def add_transaction(new_transaction):
    try:
        if "tranzakcio_id" not in new_transaction:
            new_transaction["tranzakcio_id"] = f"{new_transaction['user_id']}_{datetime.now().strftime('%Y%m%d')}_{int(time.time())}"
            
        result = db.transactions.insert_one(new_transaction)
        return result.inserted_id is not None
    except Exception as e:
        st.error(f"Error adding transaction: {e}")
        return False

def update_transaction(transaction_id, updated_data):
    try:
        result = db.transactions.update_one(
            {"tranzakcio_id": transaction_id},
            {"$set": updated_data}
        )
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Error updating transaction: {e}")
        return False

def delete_transaction(transaction_id):
    try:
        result = db.transactions.delete_one({"tranzakcio_id": transaction_id})
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Error deleting transaction: {e}")
        return False

def log_transaction_change(user_id, action, transaction_id, old_values=None, new_values=None):
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_id": str(user_id),
        "action": action,
        "transaction_id": transaction_id,
        "old_values": str(old_values) if old_values else None,
        "new_values": str(new_values) if new_values else None
    }
    
    db.transaction_logs.insert_one(log_data)

#%% Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.df = load_data()
    
    with st.expander("Debug DataFrame Info"):
        st.write("DataFrame columns:", st.session_state.df.columns.tolist())
        st.write("First few rows:", st.session_state.df.head())
    
    # Típuskonverziók csak akkor, ha van adat
    if not st.session_state.df.empty:
        numeric_columns = ['assets', 'befektetes', 'likvid', 'megtakaritas', 'osszeg']
        for col in numeric_columns:
            if col in st.session_state.df.columns:
                st.session_state.df[col] = pd.to_numeric(st.session_state.df[col], errors='coerce').fillna(0)
    
    st.session_state.accounts = load_accounts()

# Main app
st.title("💰 NestCash prototípus")

# Login/Registration
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
                if db.users.find_one({"username": new_username}):
                    st.error("Ez a felhasználónév már foglalt!")
                elif new_password != confirm_password:
                    st.error("A jelszavak nem egyeznek!")
                else:
                    last_user = db.users.find_one(sort=[("user_id", -1)])
                    new_user_id = 1 if last_user is None else last_user["user_id"] + 1
                    
                    while db.users.find_one({"user_id": new_user_id}) is not None:
                        new_user_id += 1
                    
                    new_user = {
                        "user_id": new_user_id,
                        "username": new_username,
                        "password": hash_password(new_password),
                        "email": email,
                        "registration_date": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    db.users.insert_one(new_user)
                    
                    st.session_state.logged_in = True
                    st.session_state.current_user = new_user
                    st.session_state.user_id = new_user_id
                    st.session_state.username = new_username
                    st.success("Sikeres regisztráció!")
                    st.rerun()
    st.stop()

# If logged in, show the main interface
if st.session_state.logged_in:
    username = st.session_state.username
    st.session_state.user_id = db.users.find_one({"username": username})['user_id']
    current_user = st.session_state.user_id
    st.success(f"Bejelentkezve mint: {username} (ID: {current_user})")
    st.header(f"Üdvözlünk, {username}!")
    
    # Show user metrics
    user_df = st.session_state.df[st.session_state.df["user_id"] == current_user]
    if user_df.empty:
        st.session_state.profil = 'alap'
    else:
        st.session_state.profil = user_df['profil'].iloc[-1]
    
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
    cols[0].metric("Likvid", f"{likvid:,.0f}Ft")
    cols[1].metric("Befektetések", f"{befektetes:,.0f}Ft")
    cols[2].metric("Megtakarítások", f"{megtakaritas:,.0f}Ft")
    
    if st.button("Kijelentkezés", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.success("Sikeresen kijelentkeztél!")
        st.rerun()