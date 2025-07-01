# app.py - Main application file
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import hashlib
import os
import json

# Common functions and session state management
# Módosítsd a fájlbetöltő függvényeket így:
def load_data():
    try:
        return pd.read_csv("datafiles/szintetikus_tranzakciok.csv")
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
    df.to_csv("datafiles/szintetikus_tranzakciok.csv", index=False)

def load_users():
    try:
        return pd.read_csv("datafiles/users.csv")
    except:
        return pd.DataFrame(columns=["user_id", "username", "password", "email", "registration_date"])

def save_users(users_df):
    users_df.to_csv("datafiles/users.csv", index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    users_df = load_users()
    hashed_pw = hash_password(password)
    user = users_df[(users_df["username"] == username) & (users_df["password"] == hashed_pw)]
    return user.iloc[0] if not user.empty else None

def load_accounts():
    try:
        with open("datafiles/accounts.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_accounts(accounts_dict):
    with open("datafiles/accounts.json", "w") as f:
        json.dump(accounts_dict, f)

def get_user_accounts(user_id):
    accounts = load_accounts()
    user_id_str = str(user_id)
    
    if user_id_str not in accounts:
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

def update_transaction(transaction_id, updated_data):
    df = load_data()
    if transaction_id in df['tranzakcio_id'].values:
        idx = df.index[df['tranzakcio_id'] == transaction_id].tolist()[0]
        for key, value in updated_data.items():
            df.at[idx, key] = value
        save_data(df)
        return True
    return False

def delete_transaction(transaction_id):
    df = load_data()
    if transaction_id in df['tranzakcio_id'].values:
        df = df[df['tranzakcio_id'] != transaction_id]
        save_data(df)
        return True
    return False

def log_transaction_change(user_id, action, transaction_id, old_values=None, new_values=None):
    try:
        log_df = pd.read_csv("datafiles/transaction_changes_log.csv")
    except:
        log_df = pd.DataFrame(columns=[
            "timestamp", "user_id", "action", "transaction_id", 
            "old_values", "new_values"
        ])
    
    new_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_id": user_id,
        "action": action,
        "transaction_id": transaction_id,
        "old_values": str(old_values) if old_values else None,
        "new_values": str(new_values) if new_values else None
    }
    
    log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
    log_df.to_csv("datafiles/transaction_changes_log.csv", index=False)
    
def update_transaction(transaction_id, updated_data):
    df = load_data()
    if transaction_id in df['tranzakcio_id'].values:
        idx = df.index[df['tranzakcio_id'] == transaction_id].tolist()[0]
        old_values = df.loc[idx].to_dict()
        
        for key, value in updated_data.items():
            df.at[idx, key] = value
        
        save_data(df)
        log_transaction_change(
            st.session_state.user_id,
            "update",
            transaction_id,
            old_values,
            df.loc[idx].to_dict()
        )
        return True
    return False

def delete_transaction(transaction_id):
    df = load_data()
    if transaction_id in df['tranzakcio_id'].values:
        old_values = df[df['tranzakcio_id'] == transaction_id].iloc[0].to_dict()
        df = df[df['tranzakcio_id'] != transaction_id]
        save_data(df)
        log_transaction_change(
            st.session_state.user_id,
            "delete",
            transaction_id,
            old_values
        )
        return True
    return False

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.df = load_data()

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
                users_df = load_users()
                
                if new_password != confirm_password:
                    st.error("A jelszavak nem egyeznek!")
                elif new_username in users_df["username"].values:
                    st.error("Ez a felhasználónév már foglalt!")
                else:
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
                    
                    st.success("Sikeres regisztráció! Automatikusan bejelentkeztél.")
                    st.rerun()
    
    st.stop()

# If logged in, show the main interface
if st.session_state.logged_in:
    current_user = st.session_state.user_id
    username = st.session_state.username
    st.success(f"Bejelentkezve mint: {username} (ID: {current_user})")
    
    # Show user metrics
    user_df = st.session_state.df[st.session_state.df["user_id"] == current_user]
    if user_df.empty:
        st.session_state.profil = 'alap'  # Alapértelmezett profil
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