# pages/5_🎯_Szokások.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go
from database import db

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

st.title("💰 NestCash prototípus")
st.success(f"👤 Bejelentkezve mint: {st.session_state.username} (ID: {current_user})")

# Metrics display
if user_df.empty:
    likvid = befektetes = megtakaritas = 0
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
st.header("🎯 Szokások követése")

# Szokáskezelő függvények
def load_habits():
    """Felhasználó szokásainak betöltése"""
    habits = list(db.habits.find({"user_id": str(current_user)}))
    return pd.DataFrame(habits) if habits else pd.DataFrame(columns=[
        "habit_id", "user_id", "title", "description", "category", 
        "frequency", "target_value", "tracking_type", "is_active",
        "created_at", "streak_count", "best_streak", "last_completed"
    ])

def save_habit(habit_data):
    """Új szokás mentése"""
    try:
        habit_data["user_id"] = str(current_user)
        habit_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        habit_data["streak_count"] = 0
        habit_data["best_streak"] = 0
        habit_data["last_completed"] = None
        
        result = db.habits.insert_one(habit_data)
        return result.inserted_id is not None
    except Exception as e:
        st.error(f"Hiba a szokás mentésekor: {e}")
        return False

def load_habit_logs():
    """Szokásnaplók betöltése"""
    logs = list(db.habit_logs.find({"user_id": str(current_user)}))
    return pd.DataFrame(logs) if logs else pd.DataFrame(columns=[
        "log_id", "user_id", "habit_id", "date", "completed", 
        "value", "notes", "created_at"
    ])

def log_habit_completion(habit_id, completed, value=None, notes=""):
    """Szokás teljesítésének naplózása"""
    try:
        today = datetime.now().date().strftime("%Y-%m-%d")
        
        # Ellenőrizzük, hogy ma már volt-e bejegyzés
        existing_log = db.habit_logs.find_one({
            "user_id": str(current_user),
            "habit_id": habit_id,
            "date": today
        })
        
        log_data = {
            "user_id": str(current_user),
            "habit_id": habit_id,
            "date": today,
            "completed": completed,
            "value": value,
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if existing_log:
            # Frissítjük a meglévő bejegyzést
            db.habit_logs.update_one(
                {"_id": existing_log["_id"]},
                {"$set": log_data}
            )
        else:
            # Új bejegyzés
            db.habit_logs.insert_one(log_data)
        
        # Streak számítás frissítése
        update_habit_streak(habit_id)
        return True
        
    except Exception as e:
        st.error(f"Hiba a szokás naplózásakor: {e}")
        return False

def update_habit_streak(habit_id):
    """Szokás streak számítás frissítése"""
    try:
        # Utolsó 30 nap logjai
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        logs = list(db.habit_logs.find({
            "user_id": str(current_user),
            "habit_id": habit_id,
            "date": {"$gte": thirty_days_ago}
        }).sort("date", -1))
        
        if not logs:
            return
        
        # Jelenlegi streak számítása
        current_streak = 0
        today = datetime.now().date()
        
        for log in logs:
            log_date = datetime.strptime(log["date"], "%Y-%m-%d").date()
            days_diff = (today - log_date).days
            
            if days_diff == current_streak and log["completed"]:
                current_streak += 1
            else:
                break
        
        # Legjobb streak keresése
        best_streak = 0
        temp_streak = 0
        
        for log in reversed(logs):
            if log["completed"]:
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Frissítés az adatbázisban
        db.habits.update_one(
            {"habit_id": habit_id, "user_id": str(current_user)},
            {
                "$set": {
                    "streak_count": current_streak,
                    "best_streak": best_streak,
                    "last_completed": logs[0]["date"] if logs and logs[0]["completed"] else None
                }
            }
        )
        
    except Exception as e:
        st.error(f"Hiba a streak frissítésekor: {e}")

def get_habit_progress(habit_id, days=30):
    """Szokás haladásának lekérése"""
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        logs = list(db.habit_logs.find({
            "user_id": str(current_user),
            "habit_id": habit_id,
            "date": {"$gte": start_date}
        }).sort("date", 1))
        
        return pd.DataFrame(logs) if logs else pd.DataFrame()
    except Exception as e:
        st.error(f"Hiba a haladás lekérésekor: {e}")
        return pd.DataFrame()

# Predefiniált szokások
PREDEFINED_HABITS = {
    "Pénzügyi szokások": [
        {"title": "Nem rendeltem ételt", "description": "Nem rendeltem ételt házhozszállítással", "category": "Pénzügyi"},
        {"title": "Bevásárló lista alapján vásároltam", "description": "Csak a listán szereplő dolgokat vettem meg", "category": "Pénzügyi"},
        {"title": "Impulzusvásárlás kerülése", "description": "Nem vásároltam spontán módon", "category": "Pénzügyi"},
        {"title": "Napi költés nyomon követése", "description": "Minden kiadást rögzítettem", "category": "Pénzügyi"},
    ],
    "Megtakarítási szokások": [
        {"title": "Napi megtakarítás", "description": "Minden nap tettem félre valamennyit", "category": "Megtakarítás"},
        {"title": "Aprópénz gyűjtés", "description": "Az aprópénzt külön gyűjtöttem", "category": "Megtakarítás"},
        {"title": "50/30/20 szabály", "description": "Betartottam a 50/30/20 költségvetési szabályt", "category": "Megtakarítás"},
    ],
    "Befektetési szokások": [
        {"title": "Befektetési hírek olvasása", "description": "Minimum 10 percet töltöttem pénzügyi hírek olvasásával", "category": "Befektetés"},
        {"title": "Portfólió áttekintése", "description": "Ellenőriztem a befektetéseim teljesítményét", "category": "Befektetés"},
    ]
}

# Fő interfész
tab1, tab2, tab3, tab4 = st.tabs(["📊 Áttekintés", "➕ Új szokás", "📝 Napi rögzítés", "📈 Statisztikák"])

with tab1:
    st.subheader("Szokások áttekintése")
    
    habits_df = load_habits()
    active_habits = habits_df[habits_df["is_active"] == True] if not habits_df.empty else pd.DataFrame()
    
    if active_habits.empty:
        st.info("Nincsenek aktív szokások. Hozz létre újat az 'Új szokás' fülön!")
    else:
        # Gyors áttekintés
        col1, col2, col3 = st.columns(3)
        
        total_habits = len(active_habits)
        avg_streak = active_habits["streak_count"].mean() if not active_habits.empty else 0
        best_streak = active_habits["best_streak"].max() if not active_habits.empty else 0
        
        col1.metric("Aktív szokások", total_habits)
        col2.metric("Átlagos streak", f"{avg_streak:.1f}")
        col3.metric("Legjobb streak", best_streak)
        
        # Szokások listája
        st.write("### Aktív szokások")
        for _, habit in active_habits.iterrows():
            with st.expander(f"{habit['title']} (🔥 {habit['streak_count']} nap)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Leírás:** {habit['description']}")
                    st.write(f"**Kategória:** {habit['category']}")
                    st.write(f"**Gyakoriság:** {habit['frequency']}")
                
                with col2:
                    st.write(f"**Jelenlegi streak:** {habit['streak_count']} nap")
                    st.write(f"**Legjobb streak:** {habit['best_streak']} nap")
                    st.write(f"**Utoljára teljesítve:** {habit['last_completed'] or 'Még soha'}")
                
                # Gyors naplózás
                col1, col2 = st.columns(2)
                if col1.button(f"✅ Teljesítve ma", key=f"complete_{habit['habit_id']}"):
                    if log_habit_completion(habit['habit_id'], True):
                        st.success("Szokás teljesítve!")
                        st.rerun()
                
                if col2.button(f"❌ Nem teljesítve", key=f"skip_{habit['habit_id']}"):
                    if log_habit_completion(habit['habit_id'], False):
                        st.info("Bejegyzés rögzítve.")
                        st.rerun()

with tab2:
    st.subheader("Új szokás hozzáadása")
    
    # Predefiniált szokások kiválasztása
    with st.expander("🔄 Predefiniált szokások"):
        for category, habits in PREDEFINED_HABITS.items():
            st.write(f"**{category}:**")
            for i, habit in enumerate(habits):
                col1, col2 = st.columns([3, 1])
                col1.write(f"• {habit['title']}")
                if col2.button("Hozzáadás", key=f"add_predefined_{category}_{i}"):
                    habit_data = {
                        "habit_id": f"{current_user}_{int(time.time())}",
                        "title": habit["title"],
                        "description": habit["description"],
                        "category": habit["category"],
                        "frequency": "Napi",
                        "target_value": 1,
                        "tracking_type": "boolean",
                        "is_active": True
                    }
                    
                    if save_habit(habit_data):
                        st.success(f"Szokás hozzáadva: {habit['title']}")
                        st.rerun()
    
    # Egyéni szokás létrehozása
    st.write("### Egyéni szokás létrehozása")
    with st.form("new_habit_form"):
        title = st.text_input("Szokás neve*")
        description = st.text_area("Leírás")
        category = st.selectbox("Kategória", ["Pénzügyi", "Megtakarítás", "Befektetés", "Egyéb"])
        frequency = st.selectbox("Gyakoriság", ["Napi", "Heti", "Havi"])
        tracking_type = st.selectbox("Követés típusa", ["boolean", "numeric"])
        
        target_value = 1
        if tracking_type == "numeric":
            target_value = st.number_input("Cél érték", min_value=1, value=1)
        
        if st.form_submit_button("Szokás létrehozása"):
            if not title.strip():
                st.error("A szokás neve kötelező!")
            else:
                habit_data = {
                    "habit_id": f"{current_user}_{int(time.time())}",
                    "title": title,
                    "description": description,
                    "category": category,
                    "frequency": frequency,
                    "target_value": target_value,
                    "tracking_type": tracking_type,
                    "is_active": True
                }
                
                if save_habit(habit_data):
                    st.success("Szokás sikeresen létrehozva!")
                    st.rerun()

with tab3:
    st.subheader("Napi szokás rögzítés")
    
    habits_df = load_habits()
    active_habits = habits_df[habits_df["is_active"] == True] if not habits_df.empty else pd.DataFrame()
    
    if active_habits.empty:
        st.info("Nincsenek aktív szokások.")
    else:
        today = datetime.now().date().strftime("%Y-%m-%d")
        
        # Ellenőrizzük, melyek vannak már ma rögzítve
        today_logs = list(db.habit_logs.find({
            "user_id": str(current_user),
            "date": today
        }))
        
        logged_habit_ids = [log["habit_id"] for log in today_logs]
        
        st.write(f"### Mai nap rögzítése ({today})")
        
        for _, habit in active_habits.iterrows():
            with st.expander(f"{habit['title']} {'✅' if habit['habit_id'] in logged_habit_ids else '⏳'}"):
                
                # Meglévő mai bejegyzés megjelenítése
                existing_log = next((log for log in today_logs if log["habit_id"] == habit["habit_id"]), None)
                
                if existing_log:
                    status = "✅ Teljesítve" if existing_log["completed"] else "❌ Nem teljesítve"
                    st.write(f"**Mai állapot:** {status}")
                    if existing_log.get("notes"):
                        st.write(f"**Jegyzet:** {existing_log['notes']}")
                
                # Rögzítési űrlap
                with st.form(f"log_habit_{habit['habit_id']}"):
                    st.write(f"**{habit['title']}**")
                    st.write(habit['description'])
                    
                    if habit['tracking_type'] == 'boolean':
                        completed = st.checkbox("Teljesítve", value=existing_log["completed"] if existing_log else False)
                        value = None
                    else:
                        completed = st.checkbox("Teljesítve", value=existing_log["completed"] if existing_log else False)
                        value = st.number_input("Érték", min_value=0, value=existing_log.get("value", 0) if existing_log else 0)
                    
                    notes = st.text_area("Jegyzet (opcionális)", value=existing_log.get("notes", "") if existing_log else "")
                    
                    if st.form_submit_button("Rögzítés"):
                        if log_habit_completion(habit['habit_id'], completed, value, notes):
                            st.success("Szokás rögzítve!")
                            st.rerun()

with tab4:
    st.subheader("Statisztikák és haladás")
    
    habits_df = load_habits()
    active_habits = habits_df[habits_df["is_active"] == True] if not habits_df.empty else pd.DataFrame()
    
    if active_habits.empty:
        st.info("Nincsenek aktív szokások.")
    else:
        # Szokás kiválasztása
        habit_titles = dict(zip(active_habits["habit_id"], active_habits["title"]))
        selected_habit_id = st.selectbox("Válassz szokást", list(habit_titles.keys()), format_func=lambda x: habit_titles[x])
        
        if selected_habit_id:
            selected_habit = active_habits[active_habits["habit_id"] == selected_habit_id].iloc[0]
            
            # Haladás lekérése
            progress_df = get_habit_progress(selected_habit_id, 30)
            
            if not progress_df.empty:
                # Napi teljesítés grafikon
                fig = px.scatter(
                    progress_df, 
                    x='date', 
                    y='completed',
                    color='completed',
                    title=f'{selected_habit["title"]} - Utolsó 30 nap',
                    labels={'completed': 'Teljesítve', 'date': 'Dátum'}
                )
                fig.update_traces(size=10)
                st.plotly_chart(fig, use_container_width=True)
                
                # Heti összesítés
                progress_df['date'] = pd.to_datetime(progress_df['date'])
                progress_df['week'] = progress_df['date'].dt.isocalendar().week
                weekly_summary = progress_df.groupby('week')['completed'].sum().reset_index()
                
                fig2 = px.bar(
                    weekly_summary, 
                    x='week', 
                    y='completed',
                    title='Heti teljesítés',
                    labels={'completed': 'Teljesített napok', 'week': 'Hét'}
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Statisztikák
                col1, col2, col3 = st.columns(3)
                
                total_days = len(progress_df)
                completed_days = progress_df['completed'].sum()
                completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
                
                col1.metric("Összes nap", total_days)
                col2.metric("Teljesített napok", completed_days)
                col3.metric("Teljesítési arány", f"{completion_rate:.1f}%")
                
            else:
                st.info("Még nincsenek rögzítések ehhez a szokáshoz.")