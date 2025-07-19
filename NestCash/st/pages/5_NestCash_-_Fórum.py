# pages/5_Fórum.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from bson import ObjectId
from database import load_data, save_data, get_collection, update_collection, db


# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
username = st.session_state.username
df = st.session_state.df
user_df = df[df["user_id"] == current_user]

# ===== MONGODB KOLLEKCIÓ FÜGGVÉNYEK =====

# Fórum posztok kezelése
def load_forum_posts():
    posts = list(db.forum_posts.find({}))
    return pd.DataFrame(posts) if posts else pd.DataFrame(columns=[
        "post_id", "user_id", "username", "timestamp", 
        "title", "content", "category", "privacy_level", "like_count", "comment_count"
    ])

# Hozzászólások kezelése
def load_comments():
    comments = list(db.forum_comments.find({}))
    return pd.DataFrame(comments) if comments else pd.DataFrame(columns=[
        "comment_id", "post_id", "user_id", "username",
        "timestamp", "content"
    ])

# Like-ok kezelése
def load_likes():
    likes = list(db.forum_likes.find({}))
    return pd.DataFrame(likes) if likes else pd.DataFrame(columns=[
        "like_id", "post_id", "user_id", "username", "timestamp"
    ])

# Követés kezelése
def load_follows():
    follows = list(db.user_follows.find({}))
    return pd.DataFrame(follows) if follows else pd.DataFrame(columns=[
        "follow_id", "follower_id", "following_id", "follower_username", 
        "following_username", "timestamp", "status"
    ])

# Értesítések kezelése
def load_notifications():
    notifications = list(db.notifications.find({}))
    return pd.DataFrame(notifications) if notifications else pd.DataFrame(columns=[
        "notification_id", "user_id", "type", "message", "related_id", 
        "from_user", "timestamp", "read", "action_url"
    ])

#%% ===== SEGÉDFÜGGVÉNYEK =====

def create_notification(user_id, notification_type, message, related_id=None, from_user=None):
    """Új értesítés létrehozása"""
    notifications_df = load_notifications()
    
    # NaN értékek kezelése
    if pd.isna(user_id) or pd.isna(from_user):
        return  # Ne hozz létre értesítést, ha valamelyik user_id NaN
    
    new_notification = {
        "notification_id": str(int(time.time() * 1000)),
        "user_id": int(user_id),  # Explicit int konverzió
        "type": notification_type,
        "message": message,
        "related_id": related_id,
        "from_user": int(from_user) if from_user is not None else None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "action_url": None
    }
    
    db.notifications.insert_one(new_notification)

def get_user_friends(user_id):
    """Felhasználó barátainak lekérése"""
    follows_df = load_follows()
    friends = follows_df[
        (follows_df["follower_id"] == user_id) & 
        (follows_df["status"] == "accepted")
    ]["following_id"].tolist()
    return friends

def can_view_post(post, viewer_id):
    """Ellenőrzi, hogy a felhasználó láthatja-e a posztot"""
    if "privacy_level" in post.keys():
        if post["privacy_level"] == "publikus":
            return True
        elif post["privacy_level"] == "privát" and post["user_id"] == viewer_id:
            return True
        elif post["privacy_level"] == "ismerősök":
            if post["user_id"] == viewer_id:
                return True
            friends = get_user_friends(post["user_id"])
            return viewer_id in friends
        return False
    else:
        return True

def toggle_like(post_id, user_id, username):
    """Like toggle funkció"""
    likes_df = load_likes()
    existing_like = likes_df[
        (likes_df["post_id"] == str(post_id)) & 
        (likes_df["user_id"] == user_id)
    ]
    
    if existing_like.empty:
        # Új like
        new_like = {
            "like_id": str(int(time.time() * 1000)),
            "post_id": str(post_id),
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        db.forum_likes.insert_one(new_like)
        
        # Értesítés létrehozása
        post = db.forum_posts.find_one({"post_id": str(post_id)})
        if post and post["user_id"] != user_id:
            create_notification(
                post["user_id"],
                "like", 
                f"{username} kedvelte a bejegyzésedet", 
                post_id, 
                user_id
            )
    else:
        # Like törlése
        db.forum_likes.delete_one({"like_id": existing_like.iloc[0]["like_id"]})
    
    # Post like count frissítése
    post_likes = db.forum_likes.count_documents({"post_id": str(post_id)})
    db.forum_posts.update_one(
        {"post_id": str(post_id)},
        {"$set": {"like_count": post_likes}}
    )
    
# Értesítés olvasottá tétele
def mark_notification_read(notification_id):
    db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {"read": True}}
    )

# Összes értesítés olvasottá tétele
def mark_all_notifications_read(user_id):
    db.notifications.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True}}
    )

# Értesítés törlése
def delete_notification(notification_id):
    db.notifications.delete_one({"notification_id": notification_id})
    
# Követés hozzáadása
def add_follow(follower_id, follower_username, following_id, following_username):
    follow_id = str(int(time.time() * 1000))
    new_follow = {
        "follow_id": follow_id,
        "follower_id": follower_id,
        "following_id": following_id,
        "follower_username": follower_username,
        "following_username": following_username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "accepted"
    }
    db.user_follows.insert_one(new_follow)
    
    # Értesítés küldése
    create_notification(
        following_id,
        "follow",
        f"{follower_username} követni kezdett téged",
        None,
        follower_id
    )
    return new_follow

# Követés törlése
def remove_follow(follower_id, following_username):
    result = db.user_follows.delete_one({
        "follower_id": follower_id,
        "following_username": following_username
    })
    return result.deleted_count > 0

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

# Értesítések száma
notifications_df = load_notifications()
unread_count = len(notifications_df[
    (notifications_df["user_id"] == current_user) & 
    (notifications_df["read"] == False)
])

st.header("")
st.header("🌐 Közösségi Fórum")

# Fül navigáció
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Főoldal", 
    f"🔔 Értesítések ({unread_count})", 
    "👥 Követés", 
    "⚙️ Beállítások"
])

# ===== FŐOLDAL TAB =====
likes_df = load_likes()
with tab1:
    # Új bejegyzés létrehozása
    with st.expander("➕ Új bejegyzés létrehozása", expanded=False):
        with st.form("new_post_form"):
            col1, col2 = st.columns(2)
            title = col1.text_input("Cím*")
            category = col2.selectbox("Kategória*", [
                "Általános", "Befektetések", "Megtakarítási tippek", 
                "Költségkezelés", "Kérdések"
            ])
            content = st.text_area("Tartalom*", height=150)
            privacy_level = st.selectbox("Adatvédelmi szint", 
                ["publikus", "ismerősök", "privát"])
            
            submitted = st.form_submit_button("Közzététel")
            
            if submitted:
                if not title or not content:
                    st.error("A csillaggal (*) jelölt mezők kitöltése kötelező!")
                else:
                    posts_df = load_forum_posts()
                    new_post_id = str(int(time.time() * 1000))
                    
                    new_post = {
                        "post_id": new_post_id,
                        "user_id": current_user,
                        "username": username,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "title": title,
                        "content": content,
                        "category": category,
                        "privacy_level": privacy_level,
                        "like_count": 0,
                        "comment_count": 0
                    }
                    
                    db.forum_posts.insert_one(new_post)
                    
                    st.success("Bejegyzés sikeresen közzétéve!")
                    st.rerun()

    # Feed testreszabása
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_category = st.selectbox("Kategória", 
            ["Összes", "Általános", "Befektetések", "Megtakarítási tippek", 
             "Költségkezelés", "Kérdések"])
    with col2:
        feed_type = st.selectbox("Feed típus", 
            ["Összes bejegyzés", "Csak követettek", "Saját bejegyzések"])
    with col3:
        sort_order = st.radio("Rendezés", 
            ["Legújabb előre", "Legnépszerűbb", "Legrégebbi előre"])

    # Bejegyzések betöltése és szűrése
    posts_df = load_forum_posts()
    comments_df = load_comments()
    likes_df = load_likes()
    
    # Adatvédelmi szűrés
    visible_posts = []
    for _, post in posts_df.iterrows():
        if can_view_post(post, current_user):
            visible_posts.append(post)
    
    if visible_posts:
        filtered_posts = pd.DataFrame(visible_posts)
        
        # Kategória szűrés
        if selected_category != "Összes":
            filtered_posts = filtered_posts[filtered_posts["category"] == selected_category]
        
        # Feed típus szűrés
        if feed_type == "Csak követettek":
            friends = get_user_friends(current_user)
            filtered_posts = filtered_posts[filtered_posts["user_id"].isin(friends)]
        elif feed_type == "Saját bejegyzések":
            filtered_posts = filtered_posts[filtered_posts["user_id"] == current_user]
        
        # Rendezés
        if sort_order == "Legújabb előre":
            filtered_posts = filtered_posts.sort_values("timestamp", ascending=False)
        elif sort_order == "Legnépszerűbb":
            filtered_posts = filtered_posts.sort_values("like_count", ascending=False)
        else:
            filtered_posts = filtered_posts.sort_values("timestamp", ascending=True)
        
        # Bejegyzések megjelenítése
        if filtered_posts.empty:
            st.info("Nincsenek megjeleníthető bejegyzések a kiválasztott szűrőkkel.")
        else:
            for _, post in filtered_posts.iterrows():
                with st.container():
                    # Post header
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        privacy_icon = {"publikus": "🌐", "ismerősök": "👥", "privát": "🔒"}
                        st.markdown(f"#### {post['title']} {privacy_icon.get(post.get('privacy_level', None), '')}")
                        st.caption(f"📅 {post['timestamp']} | 👤 {post['username']} | 🏷️ {post['category']}")
                    
                    # Like gomb
                    with col2:
                        user_liked = not likes_df[
                            (likes_df["post_id"] == str(post["post_id"])) & 
                            (likes_df["user_id"] == current_user)
                        ].empty
                        
                        like_button_text = "❤️" if user_liked else "🤍"
                        if st.button(f"{like_button_text} {post.get('like_count', 0):.0f}", 
                                   key=f"like_{post['post_id']}"):
                            toggle_like(post["post_id"], current_user, username)
                            st.rerun()
                    
                    # Törlés gomb (csak a saját posztoknál jelenik meg)
                    with col3:
                        if post['user_id'] == current_user:
                            if st.button("🗑️", key=f"delete_{post['post_id']}", help="Bejegyzés törlése"):
                                post_id_to_delete = post["post_id"]
                                
                                # Poszt, hozzászólások és like-ok törlése az adatbázisból
                                db.forum_posts.delete_one({"post_id": post_id_to_delete})
                                db.forum_comments.delete_many({"post_id": post_id_to_delete})
                                db.forum_likes.delete_many({"post_id": post_id_to_delete})
                                
                                st.success("A bejegyzés és a hozzá tartozó adatok sikeresen törölve!")
                                st.rerun()
                    
                    # Post content
                    st.markdown(post['content'])
                    
                    # Hozzászólások
                    post_comments = comments_df[comments_df["post_id"] == post["post_id"]]
                    comment_count = len(post_comments)
                    
                    with st.expander(f"💬 Hozzászólások ({comment_count})", expanded=False):
                        # Meglévő hozzászólások
                        if not post_comments.empty:
                            for _, comment in post_comments.sort_values("timestamp").iterrows():
                                st.markdown(f"**{comment['username']}** ({comment['timestamp']}):")
                                st.markdown(comment['content'])
                                st.divider()
                        
                        # Új hozzászólás
                        with st.form(key=f"comment_form_{post['post_id']}"):
                            new_comment = st.text_area("Új hozzászólás", 
                                                     key=f"comment_{post['post_id']}")
                            submitted = st.form_submit_button("Hozzászólás küldése")
                            
                            if submitted and new_comment:
                                new_comment_id = str(int(time.time() * 1000))
                                
                                new_comment_row = {
                                    "comment_id": new_comment_id,
                                    "post_id": post["post_id"],
                                    "user_id": current_user,
                                    "username": username,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "content": new_comment
                                }
                                
                                db.forum_comments.insert_one(new_comment_row)
                                
                                # Értesítés a poszt szerzőjének
                                if post["user_id"] != current_user:
                                    create_notification(
                                        post["user_id"], 
                                        "comment", 
                                        f"{username} hozzászólt a bejegyzésedhez", 
                                        post["post_id"], 
                                        current_user
                                    )
                                
                                st.success("Hozzászólás elküldve!")
                                st.rerun()
                    
                    st.divider()
    else:
        st.info("Nincsenek megjeleníthető bejegyzések.")

# ===== ÉRTESÍTÉSEK TAB =====
with tab2:
    st.subheader("🔔 Értesítések")
    
    unread_count = db.notifications.count_documents({
        "user_id": current_user,
        "read": False
    })
    
    if unread_count > 0:
        if st.button("Összes megjelölése olvasottként"):
            mark_all_notifications_read(current_user)
            st.rerun()
    
    user_notifications = list(db.notifications.find(
        {"user_id": current_user},
        sort=[("timestamp", -1)]
    ))
    
    if not user_notifications:
        st.info("Nincsenek értesítések.")
    else:
        for notification in user_notifications:
            read_status = "(Olvasott)" if notification.get("read", False) else "(! Új)"
            st.markdown(f"{read_status} **{notification['message']}**")
            st.caption(f"📅 {notification['timestamp']}")
            
            if not notification.get("read", False):
                if st.button("Megjelölés olvasottként", 
                           key=f"read_{notification['notification_id']}"):
                    mark_notification_read(notification['notification_id'])
                    st.rerun()
            
            if st.button("Törlés", key=f"delete_{notification['notification_id']}"):
                delete_notification(notification['notification_id'])
                st.rerun()
            
            st.divider()

# ===== KÖVETÉS TAB =====
with tab3:
    st.subheader("👥 Követés kezelése")
    
    # Követés keresése
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Felhasználók keresése")
        search_user = st.text_input("Felhasználónév keresése")
        
        if search_user:
            # Felhasználók keresése közvetlenül az adatbázisból
            matching_users = db.forum_posts.distinct("username", 
                {"username": {"$regex": search_user, "$options": "i"}})
            
            for user in matching_users:
                if user != username:
                    col_user, col_button = st.columns([3, 1])
                    with col_user:
                        st.write(f"👤 {user}")
                    with col_button:
                        # Ellenőrzi, hogy már követi-e
                        is_following = db.user_follows.count_documents({
                            "follower_id": current_user,
                            "following_username": user
                        }) > 0
                        
                        if is_following:
                            if st.button("Követés megszüntetése", key=f"unfollow_{user}"):
                                if remove_follow(current_user, user):
                                    st.success(f"Már nem követed {user}-t")
                                    st.rerun()
                        else:
                            if st.button("Követés", key=f"follow_{user}"):
                                # Felhasználó ID lekérése
                                user_data = db.forum_posts.find_one(
                                    {"username": user},
                                    {"user_id": 1}
                                )
                                if user_data:
                                    add_follow(
                                        current_user,
                                        username,
                                        user_data["user_id"],
                                        user
                                    )
                                    st.success(f"Követed {user}-t!")
                                    st.rerun()
    
    with col2:
        st.markdown("#### Követettek listája")
        my_follows = list(db.user_follows.find(
            {"follower_id": current_user},
            {"following_username": 1}
        ))
        
        if not my_follows:
            st.info("Még nem követsz senkit.")
        else:
            for follow in my_follows:
                st.write(f"👤 {follow['following_username']}")
                if st.button("Követés megszüntetése", key=f"unfollow_list_{follow['following_username']}"):
                    if remove_follow(current_user, follow['following_username']):
                        st.rerun()

# ===== BEÁLLÍTÁSOK TAB =====
with tab4:
    st.subheader("⚙️ Közösségi beállítások")
    
    with st.form("social_settings"):
        st.markdown("#### Alapértelmezett adatvédelmi szint")
        default_privacy = st.selectbox(
            "Új bejegyzések alapértelmezett láthatósága",
            ["publikus", "ismerősök", "privát"],
            index=0
        )
        
        st.markdown("#### Értesítési beállítások")
        notify_likes = st.checkbox("Értesítés like-okról", value=True)
        notify_comments = st.checkbox("Értesítés hozzászólásokról", value=True)
        notify_follows = st.checkbox("Értesítés új követőkről", value=True)
        
        if st.form_submit_button("Beállítások mentése"):
            # Itt mentenéd a beállításokat a user_settings kollekkcióba
            st.success("Beállítások mentve!")
    
    st.markdown("#### Statisztikák")
    my_posts = len(posts_df[posts_df["user_id"] == current_user])
    my_likes = len(likes_df[likes_df["user_id"] == current_user])
    follows_df = load_follows()
    my_followers = len(follows_df[follows_df["following_id"] == current_user])
    my_following = len(follows_df[follows_df["follower_id"] == current_user])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bejegyzések", my_posts)
    col2.metric("Adott like-ok", my_likes)
    col3.metric("Követők", my_followers)
    col4.metric("Követettek", my_following)