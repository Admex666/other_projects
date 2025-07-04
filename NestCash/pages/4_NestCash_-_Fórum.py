import streamlit as st
import pandas as pd
from datetime import datetime
from database import load_data, save_data, get_collection, update_collection, db

# Get data from session state
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

current_user = st.session_state.user_id
username = st.session_state.username
df = st.session_state.df
user_df = df[df["user_id"] == current_user]


# Adatbetöltési függvények
# Módosítsd a fórum fájlkezelő függvényeket:
# Fórum posztok kezelése MongoDB-vel
def load_forum_posts():
    posts = list(db.forum_posts.find({}))
    return pd.DataFrame(posts) if posts else pd.DataFrame(columns=[
        "post_id", "user_id", "username", "timestamp", 
        "title", "content", "category"
    ])

def save_forum_posts(posts_df):
    # Töröljük a régi posztokat
    db.forum_posts.delete_many({})
    
    if not posts_df.empty:
        # Új posztok beszúrása
        db.forum_posts.insert_many(posts_df.to_dict("records"))

# Hozzászólások kezelése
def load_comments():
    comments = list(db.forum_comments.find({}))
    return pd.DataFrame(comments) if comments else pd.DataFrame(columns=[
        "comment_id", "post_id", "user_id", "username",
        "timestamp", "content"
    ])

def save_comments(comments_df):
    # Töröljük a régi hozzászólásokat
    db.forum_comments.delete_many({})
    
    if not comments_df.empty:
        # Új hozzászólások beszúrása
        db.forum_comments.insert_many(comments_df.to_dict("records"))

# Fő fórum oldal
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
st.header("💬 Közösségi Fórum")

# Kategóriák
categories = [
    "Általános",
    "Befektetések",
    "Megtakarítási tippek",
    "Költségkezelés",
    "Kérdések"
]

# Új bejegyzés létrehozása
with st.expander("➕ Új bejegyzés létrehozása", expanded=False):
    with st.form("new_post_form"):
        col1, col2 = st.columns(2)
        title = col1.text_input("Cím*")
        category = col2.selectbox("Kategória*", categories)
        content = st.text_area("Tartalom*", height=150)
        
        submitted = st.form_submit_button("Közzététel")
        
        # Új bejegyzés létrehozásának javított része
        if submitted:
            if not title or not content:
                st.error("A csillaggal (*) jelölt mezők kitöltése kötelező!")
            else:
                posts_df = load_forum_posts()
                new_post_id = str(posts_df["post_id"].max() + 1)
                # MongoDB-ben egyedi ID generálása
                new_post = {
                    "post_id": new_post_id,
                    "user_id": current_user,
                    "username": username,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "title": title,
                    "content": content,
                    "category": category
                }
                
                # Beszúrás és az automatikusan generált _id lekérése
                db.forum_posts.insert_one(new_post)
                
                st.success("Bejegyzés sikeresen közzétéve!")
                st.rerun()

# Bejegyzések megjelenítése
st.subheader("Legutóbbi bejegyzések")
posts_df = load_forum_posts()
comments_df = load_comments()

# Szűrés és rendezés
col1, col2 = st.columns(2)
with col1:
    selected_category = st.selectbox("Kategória", ["Összes"] + categories)
with col2:
    sort_order = st.radio("Rendezés", ["Legújabb elől", "Legrégebbi elől"])

# Szűrés alkalmazása
if selected_category != "Összes":
    filtered_posts = posts_df[posts_df["category"] == selected_category]
else:
    filtered_posts = posts_df

# Rendezés alkalmazása
if sort_order == "Legújabb elől":
    filtered_posts = filtered_posts.sort_values("timestamp", ascending=False)
else:
    filtered_posts = filtered_posts.sort_values("timestamp", ascending=True)

# Bejegyzések megjelenítése
if filtered_posts.empty:
    st.info("Még nincsenek bejegyzések ebben a kategóriában.")
else:
    for _, post in filtered_posts.iterrows():
        with st.container():
            st.markdown(f"#### {post['title']}")
            st.caption(f"📅 {post['timestamp']} | 👤 {post['username']} | 🏷️ {post['category']}")
            st.markdown(post['content'])
            
            # Hozzászólások szekció
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
                    new_comment = st.text_area("Új hozzászólás", key=f"comment_{post['post_id']}")
                    submitted = st.form_submit_button("Hozzászólás küldése")
                    
                    if submitted and new_comment:
                        new_comment_id = comments_df["comment_id"].max() + 1 if not comments_df.empty else 1
                        
                        new_comment_row = {
                            "comment_id": new_comment_id,
                            "post_id": post["post_id"],
                            "user_id": current_user,
                            "username": username,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "content": new_comment
                        }
                        
                        comments_df = pd.concat([comments_df, pd.DataFrame([new_comment_row])], ignore_index=True)
                        save_comments(comments_df)
                        st.success("Hozzászólás elküldve!")
                        st.rerun()
            
            st.divider()