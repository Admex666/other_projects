import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import load_data, save_data, get_collection, update_collection, db
import plotly.express as px
import plotly.graph_objects as go

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
username = st.session_state.username
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

#%% ===== ADATBETÖLTŐ FÜGGVÉNYEK =====

def load_notifications():
    notifications = list(db.notifications.find({}))
    return pd.DataFrame(notifications) if notifications else pd.DataFrame(columns=[
        "notification_id", "user_id", "type", "message", "related_id", 
        "from_user", "from_username", "timestamp", "read", "action_url"
    ])

def save_notifications(notifications_df):
    db.notifications.delete_many({})
    if not notifications_df.empty:
        db.notifications.insert_many(notifications_df.to_dict("records"))

def load_notification_settings():
    settings = list(db.notification_settings.find({"user_id": current_user}))
    if settings:
        return settings[0]
    return {
        "user_id": current_user,
        "email_notifications": True,
        "push_notifications": True,
        "like_notifications": True,
        "comment_notifications": True,
        "follow_notifications": True,
        "mention_notifications": True,
        "digest_frequency": "daily"
    }

def save_notification_settings(settings):
    db.notification_settings.update_one(
        {"user_id": current_user},
        {"$set": settings},
        upsert=True
    )

def mark_notification_read(notification_id):
    """Egyedi értesítés megjelölése olvasottként"""
    notifications_df = load_notifications()
    notifications_df.loc[
        notifications_df["notification_id"] == notification_id, "read"
    ] = True
    save_notifications(notifications_df)

def mark_all_read():
    """Összes értesítés megjelölése olvasottként"""
    notifications_df = load_notifications()
    notifications_df.loc[
        notifications_df["user_id"] == current_user, "read"
    ] = True
    save_notifications(notifications_df)

def delete_notification(notification_id):
    """Értesítés törlése"""
    notifications_df = load_notifications()
    notifications_df = notifications_df[
        notifications_df["notification_id"] != notification_id
    ]
    save_notifications(notifications_df)

def get_notification_stats():
    """Értesítési statisztikák"""
    notifications_df = load_notifications()
    user_notifications = notifications_df[notifications_df["user_id"] == current_user]
    
    if user_notifications.empty:
        return {
            "total": 0,
            "unread": 0,
            "today": 0,
            "this_week": 0,
            "by_type": {}
        }
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Dátum konvertálás
    user_notifications['date'] = pd.to_datetime(user_notifications['timestamp']).dt.date
    
    stats = {
        "total": len(user_notifications),
        "unread": len(user_notifications[user_notifications["read"] == False]),
        "today": len(user_notifications[user_notifications['date'] == today]),
        "this_week": len(user_notifications[user_notifications['date'] >= week_ago]),
        "by_type": user_notifications['type'].value_counts().to_dict()
    }
    
    return stats

def create_test_notifications():
    """Teszt értesítések létrehozása"""
    test_notifications = [
        {
            "notification_id": f"test_{current_user}_1",
            "user_id": current_user,
            "type": "like",
            "message": "TesztUser kedvelte a bejegyzésedet",
            "related_id": "test_post_1",
            "from_user": "test_user_1",
            "from_username": "TesztUser",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "read": False,
            "action_url": None
        },
        {
            "notification_id": f"test_{current_user}_2",
            "user_id": current_user,
            "type": "comment",
            "message": "MásikUser hozzászólt a bejegyzésedhez",
            "related_id": "test_post_2",
            "from_user": "test_user_2",
            "from_username": "MásikUser",
            "timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "read": False,
            "action_url": None
        },
        {
            "notification_id": f"test_{current_user}_3",
            "user_id": current_user,
            "type": "follow",
            "message": "HarmadikUser követni kezdett téged",
            "related_id": None,
            "from_user": "test_user_3",
            "from_username": "HarmadikUser",
            "timestamp": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "read": True,
            "action_url": None
        }
    ]
    
    notifications_df = load_notifications()
    for test_notif in test_notifications:
        if notifications_df[notifications_df["notification_id"] == test_notif["notification_id"]].empty:
            notifications_df = pd.concat([notifications_df, pd.DataFrame([test_notif])], ignore_index=True)
    
    save_notifications(notifications_df)

#%% ===== MAIN APP =====

# Fejléc
st.title("💰 NestCash prototípus")
st.success(f"👤 Bejelentkezve mint: {st.session_state.username} (ID: {current_user})")

# Metrikus adatok
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
st.header("🔔 Értesítési Központ")

# Statisztikák betöltése
stats = get_notification_stats()

# Gyors műveletek
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📖 Összes megjelölése olvasottként"):
        mark_all_read()
        st.success("Összes értesítés megjelölve olvasottként!")
        st.rerun()

with col2:
    if st.button("🗑️ Olvasottak törlése"):
        notifications_df = load_notifications()
        notifications_df = notifications_df[~(
            (notifications_df["user_id"] == current_user) & 
            (notifications_df["read"] == True)
        )]
        save_notifications(notifications_df)
        st.success("Olvasott értesítések törölve!")
        st.rerun()

with col3:
    if st.button("🔄 Frissítés"):
        st.rerun()

with col4:
    if st.button("⚙️ Beállítások"):
        st.session_state.show_settings = not st.session_state.get('show_settings', False)

# Statisztikák megjelenítése
st.subheader("📊 Értesítési statisztikák")

col1, col2, col3, col4 = st.columns(4)
col1.metric("📬 Összes értesítés", stats["total"])
col2.metric("🔔 Olvasatlan", stats["unread"])
col3.metric("📅 Mai nap", stats["today"])
col4.metric("🗓️ Ezen a héten", stats["this_week"])

# Típusok szerinti bontás
if stats["by_type"]:
    st.subheader("📈 Értesítések típusok szerint")
    
    type_names = {
        "like": "👍 Kedvelések",
        "comment": "💬 Hozzászólások",
        "follow": "👥 Követések",
        "mention": "🏷️ Megemlítések",
        "system": "⚙️ Rendszer"
    }
    
    chart_data = []
    for notif_type, count in stats["by_type"].items():
        chart_data.append({
            "Típus": type_names.get(notif_type, notif_type),
            "Darab": count
        })
    
    fig = px.pie(chart_data, values="Darab", names="Típus", 
                 title="Értesítések megoszlása típusok szerint")
    st.plotly_chart(fig, use_container_width=True)

# Beállítások panel
if st.session_state.get('show_settings', False):
    st.subheader("⚙️ Értesítési beállítások")
    
    settings = load_notification_settings()
    
    with st.form("notification_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Általános beállítások")
            email_notifications = st.checkbox("📧 Email értesítések", value=settings.get("email_notifications", True))
            push_notifications = st.checkbox("📱 Push értesítések", value=settings.get("push_notifications", True))
            
            st.markdown("#### Értesítési gyakoriság")
            digest_frequency = st.selectbox("Összefoglaló küldése", 
                                          ["never", "daily", "weekly", "monthly"],
                                          index=["never", "daily", "weekly", "monthly"].index(settings.get("digest_frequency", "daily")))
        
        with col2:
            st.markdown("#### Típusok szerinti beállítások")
            like_notifications = st.checkbox("👍 Kedvelések", value=settings.get("like_notifications", True))
            comment_notifications = st.checkbox("💬 Hozzászólások", value=settings.get("comment_notifications", True))
            follow_notifications = st.checkbox("👥 Követések", value=settings.get("follow_notifications", True))
            mention_notifications = st.checkbox("🏷️ Megemlítések", value=settings.get("mention_notifications", True))
        
        if st.form_submit_button("💾 Beállítások mentése"):
            new_settings = {
                "user_id": current_user,
                "email_notifications": email_notifications,
                "push_notifications": push_notifications,
                "like_notifications": like_notifications,
                "comment_notifications": comment_notifications,
                "follow_notifications": follow_notifications,
                "mention_notifications": mention_notifications,
                "digest_frequency": digest_frequency
            }
            save_notification_settings(new_settings)
            st.success("Beállítások mentve!")
            st.rerun()

# Értesítések megjelenítése
st.subheader("📋 Értesítések listája")

# Szűrők
col1, col2, col3 = st.columns(3)
with col1:
    filter_type = st.selectbox("Típus szűrő", 
                               ["Összes", "like", "comment", "follow", "mention", "system"])
with col2:
    filter_status = st.selectbox("Státusz szűrő", 
                                ["Összes", "Olvasatlan", "Olvasott"])
with col3:
    sort_order = st.selectbox("Rendezés", 
                             ["Legújabb elől", "Legrégebbi elől"])

# Értesítések betöltése és szűrése
notifications_df = load_notifications()
user_notifications = notifications_df[notifications_df["user_id"] == current_user]

if not user_notifications.empty:
    # Típus szűrés
    if filter_type != "Összes":
        user_notifications = user_notifications[user_notifications["type"] == filter_type]
    
    # Státusz szűrés
    if filter_status == "Olvasatlan":
        user_notifications = user_notifications[user_notifications["read"] == False]
    elif filter_status == "Olvasott":
        user_notifications = user_notifications[user_notifications["read"] == True]
    
    # Rendezés
    ascending = sort_order == "Legrégebbi elől"
    user_notifications = user_notifications.sort_values("timestamp", ascending=ascending)

# Értesítések megjelenítése
if user_notifications.empty:
    st.info("Nincsenek értesítések a kiválasztott szűrőkkel.")
else:
    for _, notification in user_notifications.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([8, 1, 1])
            
            with col1:
                # Ikon és státusz
                type_icons = {
                    "like": "👍",
                    "comment": "💬",
                    "follow": "👥",
                    "mention": "🏷️",
                    "system": "⚙️"
                }
                
                icon = type_icons.get(notification["type"], "🔔")
                read_status = "✅" if notification["read"] else "🔔"
                
                st.markdown(f"{icon} {read_status} **{notification['message']}**")
                st.caption(f"📅 {notification['timestamp']}")
            
            with col2:
                if not notification["read"]:
                    if st.button("📖", key=f"read_{notification['notification_id']}", 
                               help="Megjelölés olvasottként"):
                        mark_notification_read(notification["notification_id"])
                        st.rerun()
            
            with col3:
                if st.button("🗑️", key=f"delete_{notification['notification_id']}", 
                           help="Értesítés törlése"):
                    delete_notification(notification["notification_id"])
                    st.rerun()
            
            st.divider()

# Összesítő információk
if not user_notifications.empty:
    st.subheader("📊 Napi aktivitás")
    
    # Napi bontás az elmúlt 7 napra
    notifications_df['date'] = pd.to_datetime(notifications_df['timestamp']).dt.date
    user_notifications_with_date = notifications_df[notifications_df["user_id"] == current_user]
    
    if not user_notifications_with_date.empty:
        # Utolsó 7 nap
        last_week = [(datetime.now().date() - timedelta(days=i)) for i in range(7)]
        
        daily_counts = []
        for date in reversed(last_week):
            count = len(user_notifications_with_date[user_notifications_with_date['date'] == date])
            daily_counts.append({"Dátum": date.strftime("%Y-%m-%d"), "Értesítések": count})
        
        if daily_counts:
            fig = px.bar(daily_counts, x="Dátum", y="Értesítések", 
                        title="Értesítések az elmúlt 7 napban")
            st.plotly_chart(fig, use_container_width=True)

# Navigáció vissza a fórumhoz
st.markdown("---")
if st.button("🔙 Vissza a fórumhoz"):
    st.switch_page("pages/5_NestCash_-_Fórum.py")