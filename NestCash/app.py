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
from database import (get_mongo_client, load_data, load_accounts, 
                      authenticate_user, hash_password, db)

#%% Execution
if __name__ == "__main__":
#%% Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.df = load_data()
        
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
        st.success(f"👤 Bejelentkezve mint: {username} (ID: {current_user})")
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
        cols[0].metric("💵 Likvid", f"{likvid:,.0f}Ft")
        cols[1].metric("📈 Befektetések", f"{befektetes:,.0f}Ft")
        cols[2].metric("🏦 Megtakarítások", f"{megtakaritas:,.0f}Ft")
        
        if st.button("Kijelentkezés", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.user_id = None
            st.session_state.username = None
            st.success("Sikeresen kijelentkeztél!")
            st.rerun()