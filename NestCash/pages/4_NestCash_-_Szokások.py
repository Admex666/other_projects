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

#%% Szokáskezelő függvények
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
        habit_data["has_goal"] = "target_value" in habit_data and "goal_period" in habit_data
        habit_data["daily_target"] = calculate_daily_target(habit_data) if habit_data["has_goal"] else None
        
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

def calculate_daily_target(habit):
    """Napi célérték kiszámítása a gyakoriság alapján"""
    if habit["frequency"] == "Napi":
        return habit["target_value"]
    elif habit["frequency"] == "Heti":
        return habit["target_value"] / 7
    elif habit["frequency"] == "Havi":
        return habit["target_value"] / 30
    return None

def update_habit_status(habit_id, is_active):
    """Szokás állapotának frissítése (aktív/inaktív)"""
    try:
        db.habits.update_one(
            {"habit_id": habit_id, "user_id": str(current_user)},
            {"$set": {"is_active": is_active}}
        )
        return True
    except Exception as e:
        st.error(f"Hiba a szokás frissítésekor: {e}")
        return False

#%% Predefiniált szokások
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Áttekintés", "➕ Új szokás", "📝 Napi rögzítés", "📈 Statisztikák", "📦 Archivált szokások"])

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
                    
                    if habit.get('has_goal'):
                        goal_text = f"{habit['target_value']} ({habit['goal_period']})"
                        if habit['tracking_type'] == 'boolean':
                            goal_text += f" ({habit['target_value']/7:.1f}/nap)" if habit['goal_period'] == 'Heti' else ""
                            goal_text += f" ({habit['target_value']/30:.1f}/nap)" if habit['goal_period'] == 'Havi' else ""
                        st.write(f"**Cél:** {goal_text}")
                
                # Gyors naplózás
                col1, col2 = st.columns(2)
                if habit['tracking_type'] == 'boolean':
                    if col1.button(f"✅ Teljesítve ma", key=f"complete_{habit['habit_id']}"):
                        if log_habit_completion(habit['habit_id'], True):
                            st.success("Szokás teljesítve!")
                            st.rerun()
                    
                    if col2.button(f"❌ Nem teljesítve", key=f"skip_{habit['habit_id']}"):
                        if log_habit_completion(habit['habit_id'], False):
                            st.info("Bejegyzés rögzítve.")
                            st.rerun()
                else:
                    value = col1.number_input("Érték", min_value=0, key=f"value_{habit['habit_id']}")
                    if col2.button("Rögzítés", key=f"log_{habit['habit_id']}"):
                        if log_habit_completion(habit['habit_id'], True, value):
                            st.success("Érték rögzítve!")
                            st.rerun()
                
                # Archiválás/Törlés gombok
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📌 Archiválás", key=f"archive_{habit['habit_id']}"):
                        st.session_state[f"confirm_archive_{habit['habit_id']}"] = True
                    
                    if st.session_state.get(f"confirm_archive_{habit['habit_id']}", False):
                        st.warning(f"Biztosan archiválni szeretnéd: {habit['title']}?")
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("Igen", key=f"archive_yes_{habit['habit_id']}"):
                                if update_habit_status(habit['habit_id'], False):
                                    st.session_state[f"confirm_archive_{habit['habit_id']}"] = False
                                    st.success("Szokás archiválva!")
                                    st.rerun()
                        with confirm_col2:
                            if st.button("Mégse", key=f"archive_no_{habit['habit_id']}"):
                                st.session_state[f"confirm_archive_{habit['habit_id']}"] = False
                                st.rerun()
                
                with col2:
                    if st.button("🗑️ Törlés", key=f"delete_{habit['habit_id']}"):
                        st.session_state[f"confirm_delete_{habit['habit_id']}"] = True
                    
                    if st.session_state.get(f"confirm_delete_{habit['habit_id']}", False):
                        st.error(f"Biztosan törölni szeretnéd: {habit['title']}?")
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("Igen", key=f"delete_yes_{habit['habit_id']}"):
                                db.habits.delete_one({"habit_id": habit['habit_id'], "user_id": str(current_user)})
                                db.habit_logs.delete_many({"habit_id": habit['habit_id'], "user_id": str(current_user)})
                                st.session_state[f"confirm_delete_{habit['habit_id']}"] = False
                                st.success("Szokás törölve!")
                                st.rerun()
                        with confirm_col2:
                            if st.button("Mégse", key=f"delete_no_{habit['habit_id']}"):
                                st.session_state[f"confirm_delete_{habit['habit_id']}"] = False
                               

with tab2:
    st.subheader("Új szokás hozzáadása")
    
    # Predefiniált szokások kiválasztása
    with st.expander("🔄 Előre meghatározott szokások"):
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
    with st.expander("### 🧑 Saját szokás létrehozása"):
        # A checkbox-ot a formon KÍVÜL helyezzük el
        has_goal = st.checkbox("Cél megadása a szokáshoz", key="has_goal")
        
        with st.form("new_habit_form"):
            title = st.text_input("Szokás neve*")
            description = st.text_area("Leírás")
            category = st.selectbox("Kategória", ["Pénzügyi", "Megtakarítás", "Befektetés", "Egyéb"])
            frequency = st.selectbox("Gyakoriság", ["Napi", "Heti", "Havi"])
            tracking_type = st.selectbox(
                "Követés típusa", 
                options=[
                    {"name": "Igen/Nem", "value": "boolean"},
                    {"name": "Számszerű", "value": "numeric"}
                ],
                format_func=lambda x: x["name"]
            )["value"]
            
            # Cél mezők megjelenítése a checkbox állapota alapján
            if st.session_state.get("has_goal", False):
                target_value = st.number_input("Cél értéke", min_value=1, value=1)
                goal_period = st.selectbox("Cél időszaka", ["Napi", "Heti", "Havi"])
            
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
                        "tracking_type": tracking_type,
                        "is_active": True
                    }
                    
                    if st.session_state.get("has_goal", False):
                        habit_data.update({
                            "target_value": target_value,
                            "goal_period": goal_period,
                            "daily_target": calculate_daily_target({
                                "frequency": frequency,
                                "target_value": target_value
                            })
                        })
                    
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
                if selected_habit['tracking_type'] == 'boolean':
                    daily_summary = progress_df.groupby(['date', 'completed']).size().unstack(fill_value=0)
                    daily_summary = daily_summary.reset_index()
                    
                    fig = px.bar(
                        daily_summary, 
                        x='date', 
                        y=[True, False] if False in daily_summary.columns else [True],
                        title=f'{selected_habit["title"]} - Utolsó 30 nap',
                        labels={'value': 'Darab', 'date': 'Dátum'},
                        color_discrete_map={True: 'green', False: 'red'},
                        barmode='group'
                    )
                    
                    # Célvonal hozzáadása boolean szokásokhoz
                    if selected_habit.get('has_goal'):
                        target_value = selected_habit['target_value']
                        if selected_habit['goal_period'] == 'Heti':
                            target_value = target_value / 7
                        elif selected_habit['goal_period'] == 'Havi':
                            target_value = target_value / 30
                            
                        fig.add_hline(
                            y=target_value,
                            line_dash="dot",
                            line_color="blue",
                            annotation_text=f"Napi cél: {target_value:.1f}",
                            annotation_position="bottom right"
                        )
                else:
                    # Numerikus szokások vizualizációja
                    fig = px.bar(
                        progress_df,
                        x='date',
                        y='value',
                        title=f'{selected_habit["title"]} - Utolsó 30 nap',
                        labels={'value': 'Érték', 'date': 'Dátum'},
                        color='completed',
                        color_discrete_map={True: 'green', False: 'red'}
                    )
                    
                    # Célvonal hozzáadása numerikus szokásokhoz
                    if selected_habit.get('has_goal'):
                        daily_target = selected_habit['daily_target']
                        fig.add_hline(
                            y=daily_target,
                            line_dash="dot",
                            line_color="blue",
                            annotation_text=f"Napi cél: {daily_target:.1f}",
                            annotation_position="bottom right"
                        )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Haladás mutatója
                if selected_habit.get('has_goal'):
                    st.subheader("Célhoz viszonyított haladás")
                    total_days = len(progress_df)
                    actual_value = progress_df['value'].sum() if selected_habit['tracking_type'] == 'numeric' else progress_df['completed'].sum()
                    
                    if selected_habit['goal_period'] == 'Napi':
                        target = selected_habit['target_value'] * total_days
                    elif selected_habit['goal_period'] == 'Heti':
                        target = selected_habit['target_value'] * (total_days / 7)
                    else:  # Havi
                        target = selected_habit['target_value'] * (total_days / 30)
                    
                    progress_percent = min(100, (actual_value / target * 100)) if target > 0 else 0
                    st.progress(progress_percent/100, text=f"Haladás: {actual_value:.1f}/{target:.1f} ({progress_percent:.1f}%)")
                            
                # Heti összesítés
                progress_df['date'] = pd.to_datetime(progress_df['date'])
                progress_df['week'] = progress_df['date'].dt.isocalendar().week
                
                if selected_habit['tracking_type'] == 'boolean':
                    weekly_summary = progress_df.groupby('week')['completed'].sum().reset_index()
                    y_column = 'completed'
                    y_title = 'Teljesített napok'
                else:
                    weekly_summary = progress_df.groupby('week')['value'].sum().reset_index()
                    y_column = 'value'
                    y_title = 'Összérték'
                
                fig2 = px.bar(
                    weekly_summary, 
                    x='week', 
                    y=y_column,
                    title='Heti teljesítés',
                    labels={y_column: y_title, 'week': 'Hét'}
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
                
with tab5:
    st.subheader("Archivált szokások")
    
    habits_df = load_habits()
    archived_habits = habits_df[habits_df["is_active"] == False] if not habits_df.empty else pd.DataFrame()
    
    if archived_habits.empty:
        st.info("Nincsenek archivált szokások.")
    else:
        for _, habit in archived_habits.iterrows():
            with st.expander(f"{habit['title']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Leírás:** {habit['description']}")
                    st.write(f"**Kategória:** {habit['category']}")
                    st.write(f"**Utoljára teljesítve:** {habit['last_completed'] or 'Még soha'}")
                
                with col2:
                    if st.button("🔙 Visszaállítás", key=f"restore_{habit['habit_id']}"):
                        if update_habit_status(habit['habit_id'], True):
                            st.success("Szokás visszaállítva!")
                            st.rerun()
                            
                    if st.button("🗑️ Törlés", key=f"delete_{habit['habit_id']}"):
                        st.session_state[f"confirm_delete_{habit['habit_id']}"] = True
                    
                    if st.session_state.get(f"confirm_delete_{habit['habit_id']}", False):
                        st.error(f"Biztosan törölni szeretnéd: {habit['title']}?")
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("Igen", key=f"delete_yes_{habit['habit_id']}"):
                                db.habits.delete_one({"habit_id": habit['habit_id'], "user_id": str(current_user)})
                                db.habit_logs.delete_many({"habit_id": habit['habit_id'], "user_id": str(current_user)})
                                st.session_state[f"confirm_delete_{habit['habit_id']}"] = False
                                st.success("Szokás törölve!")
                                st.rerun()
                        with confirm_col2:
                            if st.button("Mégse", key=f"delete_no_{habit['habit_id']}"):
                                st.session_state[f"confirm_delete_{habit['habit_id']}"] = False