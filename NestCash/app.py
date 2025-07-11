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

def post_badge_achievement(user_id, username, badge_name, tier_name, reward):
    # Ellenőrizzük, hogy ez a kitűző/szint kombináció már posztolva lett-e a felhasználónak
    # Ehhez feltételezzük, hogy van egy 'user_badge_posts' kollekció a MongoDB-ben
    # Amiben tároljuk, hogy mely felhasználó melyik kitűzőjéről (név + szint) posztoltunk már.

    # Először is, ellenőrizzük, hogy a user_id nem None vagy NaN
    if user_id is None or pd.isna(user_id):
        return

    # Ideiglenes megoldás, ha a user_id nem int, hanem pl. ObjectId jön valahonnan
    try:
        user_id = int(user_id)
    except ValueError:
        st.error(f"Érvénytelen user_id formátum: {user_id}")
        return

    post_identifier = f"{badge_name} - {tier_name}" # Egyedi azonosító a poszthoz

    existing_post_record = db.user_badge_posts.find_one({
        "user_id": user_id,
        "badge_identifier": post_identifier
    })

    if not existing_post_record:
        # Ha még nem posztoltuk, akkor hozzuk létre a posztot
        new_post_id = str(int(time.time() * 1000))

        post_title = f"{username} megszerezte a {tier_name} ({badge_name}) kitűzőt!"
        post_content = f"{tier_name}: {reward}"

        new_forum_post = {
            "post_id": new_post_id,
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": post_title,
            "content": post_content,
            "category": "Kitűzők", # Új kategória a fórumon, vagy választhatsz meglévőt
            "privacy_level": "publikus", # Vagy "ismerősök", "privát"
            "like_count": 0,
            "comment_count": 0
        }

        db.forum_posts.insert_one(new_forum_post)

        # Rögzítsük, hogy erről a kitűzőről már posztoltunk
        db.user_badge_posts.insert_one({
            "user_id": user_id,
            "badge_identifier": post_identifier,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        st.success(f"Sikeresen posztoltad a fórumba: {post_title}") # Itt egy visszajelzés a felhasználónak
        
#%% Execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Főmenü",  # Böngészőlapon megjelenő cím
        page_icon="",         # Opcionális ikon (pl. emoji vagy fájl)
        layout="wide"                 # Opcionális elrendezés
    )

    # Initialize session state
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
        if st.button("Kijelentkezés", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.user_id = None
            st.session_state.username = None
            st.success("Sikeresen kijelentkeztél!")
            st.rerun()
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
        
        
            
st.header("")
st.header("👤 Profil")

with st.expander("**🏆 Kitűzők**", expanded=True):
    # Load user data for badge calculations
    user_transactions = st.session_state.df[st.session_state.df["user_id"] == current_user]
    user_habits = list(db.habits.find({"user_id": str(current_user)}))
    user_posts = list(db.forum_posts.find({"user_id": current_user}))
    user_follows = list(db.user_follows.find({"follower_id": current_user}))
    
    
    # Calculate badge metrics
    def calculate_badge_metrics():
        lessons_completed_count = db.lesson_completions.count_documents({
                "user_id": current_user, 
                "completed": True
            })
        
        quizzes_completed_count = db.lesson_completions.count_documents({
                "user_id": current_user,
                "quiz_score": {"$ne": None}  # $ne = not equal (nem egyenlő)
            })
        
        metrics = {
            "transactions_days": user_transactions['datum'].nunique() if not user_transactions.empty else 0,
            "savings_rate": round(1 - (user_transactions[user_transactions['bev_kiad_tipus'] != 'bevetel']['osszeg'].abs().sum() / 
                user_transactions[user_transactions['bev_kiad_tipus'] == 'bevetel']['osszeg'].sum()), 3) \
                if not user_transactions.empty else 0,
            "active_habits": len([h for h in user_habits if h.get("is_active", True)]),
            "habit_streak": max([h.get("best_streak", 0) for h in user_habits]) if user_habits else 0,
            "forum_posts": len(user_posts),
            "following_count": len(user_follows),
            "lessons_completed": lessons_completed_count,
            "quizzes_completed": quizzes_completed_count,  # Placeholder
        }
        
        return metrics
        
    def check_and_update_badges(metrics):
        # Előző badge állapot betöltése
        previous_badge_state = db.user_badge_progress.find_one({"user_id": current_user}) or {}
        
        # Badge definíciók
        badge_definitions = {
            "learning": {
                "lessons": {
                    "name": "📚 Tudásgyűjtő",
                    "icon": "📚",
                    "desc": "Tanulási anyagok elvégzése",
                    "current_value": metrics["lessons_completed"],
                    "tiers": [
                        {"requirement": 1, "name": "Tudáscsíra", "reward": "Első lecke elvégzése"},
                        {"requirement": 5, "name": "Tanuló", "reward": "5 lecke elvégzése"},
                        {"requirement": 15, "name": "Tudásvágy", "reward": "15 lecke elvégzése"},
                        {"requirement": 30, "name": "Tudásmester", "reward": "30 lecke elvégzése"},
                    ]
                },
                "quizzes": {
                    "name": "🎯 Kvízharcos",
                    "icon": "🎯",
                    "desc": "Kvízek sikeres kitöltése",
                    "current_value": metrics["quizzes_completed"],
                    "tiers": [
                        {"requirement": 1, "name": "Első Kvíz", "reward": "Első kvíz kitöltése"},
                        {"requirement": 5, "name": "Kvízkedvelő", "reward": "5 kvíz kitöltése"},
                        {"requirement": 15, "name": "Kvízharcos", "reward": "15 kvíz kitöltése"},
                        {"requirement": 25, "name": "Kvízmester", "reward": "25 kvíz kitöltése"},
                    ]
                }
            },
            "saving": {
                "amount": {
                    "name": "💰 Spóroló",
                    "icon": "💰",
                    "desc": "Megtakarított összeg",
                    "current_value": metrics["savings_rate"],
                    "tiers": [
                        {"requirement": 0.10, "name": "Fillérgyűjtő", "reward": "10% megtakarítási ráta"},
                        {"requirement": 0.17, "name": "Spóroló", "reward": "17% megtakarítási ráta"},
                        {"requirement": 0.24, "name": "Takarékos", "reward": "24% megtakarítási ráta"},
                        {"requirement": 0.31, "name": "Megtakarítás Mestere", "reward": "31% megtakarítási ráta"},
                    ]
                },
                "tracking": {
                    "name": "📊 Nyomonkövető",
                    "icon": "📊",
                    "desc": "Tranzakciók rögzítése",
                    "current_value": metrics["transactions_days"],
                    "tiers": [
                        {"requirement": 1, "name": "Első Rögzítés", "reward": "Első tranzakció rögzítése"},
                        {"requirement": 7, "name": "Heti Rendszeresség", "reward": "7 napos nyomon követés"},
                        {"requirement": 30, "name": "Havi Rendszeresség", "reward": "30 napos nyomon követés"},
                        {"requirement": 90, "name": "Elkötelezett", "reward": "90 napos nyomon követés"},
                        {"requirement": 180, "name": "Nyomon követés Mestere", "reward": "180 napos nyomon követés"},
                    ]
                }
            },
            "habit": {
                "creation": {
                    "name": "🔄 Szokásépítő",
                    "icon": "🔄",
                    "desc": "Szokások létrehozása",
                    "current_value": len(user_habits),
                    "tiers": [
                        {"requirement": 1, "name": "Első Szokás", "reward": "Első szokás létrehozása"},
                        {"requirement": 3, "name": "Szokásgyűjtő", "reward": "3 szokás létrehozása"},
                        {"requirement": 5, "name": "Szokásmester", "reward": "5 szokás létrehozása"},
                        {"requirement": 10, "name": "Szokásguru", "reward": "10 szokás létrehozása"},
                    ]
                },
                "streak": {
                    "name": "⚡ Kitartó",
                    "icon": "⚡",
                    "desc": "Leghosszabb szokás sorozat",
                    "current_value": metrics["habit_streak"],
                    "tiers": [
                        {"requirement": 3, "name": "Kezdő Kitartás", "reward": "3 napos sorozat"},
                        {"requirement": 7, "name": "Heti Kitartás", "reward": "7 napos sorozat"},
                        {"requirement": 21, "name": "Szokássá Váló", "reward": "21 napos sorozat"},
                        {"requirement": 66, "name": "Megszilárdult", "reward": "66 napos sorozat"},
                    ]
                }
            },
            "community": {
                "posts": {
                    "name": "💬 Beszélgetős",
                    "icon": "💬",
                    "desc": "Fórum bejegyzések",
                    "current_value": metrics["forum_posts"],
                    "tiers": [
                        {"requirement": 1, "name": "Első Hang", "reward": "Első fórum bejegyzés"},
                        {"requirement": 5, "name": "Aktív Tag", "reward": "5 fórum bejegyzés"},
                        {"requirement": 15, "name": "Beszélgetős", "reward": "15 fórum bejegyzés"},
                        {"requirement": 50, "name": "Közösség Motorja", "reward": "50 fórum bejegyzés"},
                    ]
                },
                "following": {
                    "name": "🤝 Kapcsolatépítő",
                    "icon": "🤝",
                    "desc": "Követett felhasználók",
                    "current_value": metrics["following_count"],
                    "tiers": [
                        {"requirement": 1, "name": "Első Kapcsolat", "reward": "Első felhasználó követése"},
                        {"requirement": 3, "name": "Társaságkedvelő", "reward": "3 felhasználó követése"},
                        {"requirement": 10, "name": "Kapcsolatépítő", "reward": "10 felhasználó követése"},
                        {"requirement": 25, "name": "Közösségi Háló", "reward": "25 felhasználó követése"},
                    ]
                }
            }
        }
        
        # Új badge szintek ellenőrzése és értesítések küldése
        for category_name, category in badge_definitions.items():
            for badge_key, badge_data in category.items():
                current_value = metrics.get(badge_key, badge_data["current_value"])
                previous_value = previous_badge_state.get(badge_key, {}).get("value", 0)
                
                current_tier, current_tier_info, _, _ = get_current_tier(current_value, badge_data["tiers"])
                previous_tier, _, _, _ = get_current_tier(previous_value, badge_data["tiers"])
                
                # Ha új szintet értünk el
                if current_tier > previous_tier and current_tier_info:
                    notification_id = str(int(time.time() * 1000))
                    new_notification = {
                        "notification_id": notification_id,
                        "user_id": current_user,
                        "type": "🎖️ Kitűzők",
                        "message": f"Gratulálunk! Megszerezted a {current_tier_info['name']} szintű {badge_data['name']} kitűzőt!",
                        "related_id": f"badge_{badge_key}_{current_tier}",
                        "from_user": 0,  # 0 = rendszer
                        "from_username": "NestCash Rendszer",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "read": False,
                        "action_url": None
                    }
                    db.notifications.insert_one(new_notification)
        
        # Jelenlegi állapot mentése
        db.user_badge_progress.update_one(
            {"user_id": current_user},
            {"$set": {
                "user_id": current_user,
                "metrics": metrics,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }},
            upsert=True
        )
        
        return badge_definitions
    
    # Define tiered badges (multi-level)
    def get_current_tier(value, tiers):
        """Get current tier and next tier info"""
        current_tier = 0
        next_tier = None
        
        for i, tier in enumerate(tiers):
            if value >= tier["requirement"]:
                current_tier = i + 1
            else:
                next_tier = tier
                break
        
        current_tier_info = tiers[current_tier - 1] if current_tier > 0 else None
        max_tier = len(tiers)
        
        return current_tier, current_tier_info, next_tier, max_tier
    
    def render_tiered_badge(badge_data):
        """Render a single tiered badge"""
        current_tier, current_tier_info, next_tier, max_tier = get_current_tier(
            badge_data["current_value"], badge_data["tiers"]
        )
    
        # Badge header
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{badge_data['icon']} {badge_data['name']}**")
            st.caption(badge_data['desc'])
        with col2:
            st.markdown(f"**{current_tier}/{max_tier}**")
    
        # Current tier info
        if current_tier > 0:
            st.success(f"✅ **{current_tier_info['name']}** - {current_tier_info['reward']}")
    
            # Posztolás gomb
            # Ellenőrizzük, hogy már posztoltunk-e erről a kitűzőről
            post_identifier = f"{badge_data['name']} - {current_tier_info['name']}"
    
            # Itt hozzáférünk a current_user és username változókhoz
            user_id_for_post = st.session_state.user_id
            username_for_post = st.session_state.username
    
            # A 'user_badge_posts' kollekció ellenőrzése
            existing_post_record = db.user_badge_posts.find_one({
                "user_id": user_id_for_post,
                "badge_identifier": post_identifier
            })
    
            if not existing_post_record:
                if st.button(f"Posztold a fórumba: {current_tier_info['name']}", 
                             key=f"post_badge_{badge_data['name']}_{current_tier_info['name']}"):
                    post_badge_achievement(
                        user_id_for_post,
                        username_for_post,
                        badge_data["name"],
                        current_tier_info["name"],
                        current_tier_info["reward"]
                    )
                    st.rerun() # Fontos, hogy újra fussuk, miután posztoltunk
            else:
                st.info("Ezt a kitűzőt már posztoltad a fórumba.")
    
        # Next tier progress (ez a rész változatlan marad)
        if next_tier:
            progress_value = badge_data["current_value"] / next_tier["requirement"]
            st.markdown(f"🎯 **Következő:** {next_tier['name']}")
            st.progress(min(1.0, progress_value))
            st.caption(f"Haladás: {badge_data['current_value']}/{next_tier['requirement']}")
        else:
            st.success("🏆 **Minden szint teljesítve!**")
    
        # Show tier progression (ez a rész változatlan marad)
        with st.expander("📊 Szintek áttekintése"):
            for i, tier in enumerate(badge_data["tiers"]):
                if i + 1 <= current_tier:
                    st.markdown(f"✅ **{i+1}. szint:** {tier['name']} ({tier['requirement']} - {tier['reward']})")
                elif i + 1 == current_tier + 1:
                    st.markdown(f"🎯 **{i+1}. szint:** {tier['name']} ({tier['requirement']} - {tier['reward']})")
                else:
                    st.markdown(f"🔒 **{i+1}. szint:** {tier['name']} ({tier['requirement']} - {tier['reward']})")

    metrics = calculate_badge_metrics()
    
    tiered_badges = check_and_update_badges(metrics)
    
    # Calculate total badges and progress
    total_current_tiers = 0
    total_possible_tiers = 0
    
    for category in tiered_badges.values():
        for badge in category.values():
            current_tier, _, _, max_tier = get_current_tier(badge["current_value"], badge["tiers"])
            total_current_tiers += current_tier
            total_possible_tiers += max_tier
    
    # Header with stats
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🏆 Kitűzők ({total_current_tiers}/{total_possible_tiers})")
    with col2:
        progress_percent = (total_current_tiers / total_possible_tiers) * 100 if total_possible_tiers > 0 else 0
        st.metric("Teljesítés", f"{progress_percent:.0f}%")
    
    # Progress bar
    st.progress(total_current_tiers / total_possible_tiers if total_possible_tiers > 0 else 0)
    
    st.markdown("---")
    
    # Badge categories
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Tanulás", "💰 Spórolás", "🔁 Szokások", "👥 Közösség"])
    
    st.markdown("---")
    
    # Render each category
    with tab1:
        for badge_data in tiered_badges["learning"].values():
            render_tiered_badge(badge_data)
    
    with tab2:
        for badge_data in tiered_badges["saving"].values():
            render_tiered_badge(badge_data)
    
    with tab3:
        for badge_data in tiered_badges["habit"].values():
            render_tiered_badge(badge_data)
    
    with tab4:
        for badge_data in tiered_badges["community"].values():
            render_tiered_badge(badge_data)
    
    # Next achievements section
    st.markdown("---")
    st.markdown("### 🎯 Legközelebbi célok")
    
    # Find next achievable badges
    next_goals = []
    for category_name, category in tiered_badges.items():
        for badge_key, badge_data in category.items():
            current_tier, _, next_tier, _ = get_current_tier(badge_data["current_value"], badge_data["tiers"])
            if next_tier:
                progress_percent = (badge_data["current_value"] / next_tier["requirement"]) * 100
                next_goals.append({
                    "name": f"{badge_data['icon']} {badge_data['name']}",
                    "next_tier": next_tier["name"],
                    "progress": progress_percent,
                    "current": badge_data["current_value"],
                    "target": next_tier["requirement"],
                    "category": category_name
                })
    
    # Sort by progress (closest to completion first)
    next_goals.sort(key=lambda x: x["progress"], reverse=True)
    
    if next_goals:
        # Show top 3 next goals
        cols = st.columns(min(3, len(next_goals)))
        for i, goal in enumerate(next_goals[:3]):
            with cols[i]:
                st.markdown(f"**{goal['name']}**")
                st.markdown(f"🎯 {goal['next_tier']}")
                st.progress(goal["progress"] / 100)
                st.caption(f"{goal['current']}/{goal['target']} ({goal['progress']:.0f}%)")
    else:
        st.success("🎉 Minden kitűző maximális szinten van!")
    
    # Motivational section
    if total_current_tiers == 0:
        st.markdown("---")
        st.info("🚀 **Kezdj bele!** Az első tranzakció rögzítésével vagy szokás létrehozásával megszerezheted az első kitűződet!")
    elif total_current_tiers < total_possible_tiers // 2:
        st.markdown("---")
        st.info(f"💪 **Jó úton jársz!** Már {total_current_tiers} szintet teljesítettél. Így tovább!")
    else:
        st.markdown("---")
        st.success(f"🌟 **Fantasztikus!** A kitűzők {progress_percent:.0f}%-át teljesítetted!")

st.header("")

st.write("### Ismerőseid")
st.write("#### (fejlesztés alatt...)")
st.header("")

st.write("### Bejegyzéseid")
st.write("#### (fejlesztés alatt...)")
st.header("")

st.write("### Kihívásaid")
st.write("#### (fejlesztés alatt...)")
st.header("")