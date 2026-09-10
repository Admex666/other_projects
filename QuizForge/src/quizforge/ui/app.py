"""QuizForge - Streamlit Vizuális Felület és DuckDB Tudásgráf Böngésző."""

import sys
from pathlib import Path

# src hozzáadása az importokhoz
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import pandas as pd
from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.storage.db import DatabaseManager
from quizforge.knowledge.relevance import RelevanceEngine
from quizforge.quiz_engine.generator import QuizGenerator
from quizforge.quiz_engine.mechanisms.abcd import ABCDMechanism
from quizforge.quiz_engine.mechanisms.estimation import EstimationMechanism

# Oldalbeállítások
st.set_page_config(
    page_title="QuizForge - Knowledge Graph & Quiz Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adatbázis elérése cache-elt kapcsolatkezelővel
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Fejléc
st.title("⚡ QuizForge – Knowledge Graph & Kvíz Platform")
st.caption("Adatvezérelt kvízfelkészítő rendszer magyar tudásgráf és Groq LLM integrációval")

# Oldalsáv
st.sidebar.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/database.svg", width=50)
st.sidebar.title("Navigáció")
menu = st.sidebar.radio(
    "Válassz modult:",
    [
        "📊 DuckDB & Gráf Böngésző",
        "🎯 Kvíz Generátor & Játék",
        "🏆 Top Kvízrelevancia",
        "👤 Játékos & Kalibráció (Hamarosan)",
    ]
)

# Groq API Valós idejű Token Figyelő az oldalsávban
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Groq API Kvóta Figyelő")
from quizforge.llm.groq_client import GroqClient
groq_client = GroqClient()

if groq_client.is_available:
    refresh_clicked = st.sidebar.button("🔄 Kvóta Lekérdezése", use_container_width=True)
    groq_quota = groq_client.get_quota_status(force_refresh=refresh_clicked)
    
    rem_tok = groq_quota.get("remaining_tokens")
    lim_tok = groq_quota.get("limit_tokens")
    rem_req = groq_quota.get("remaining_requests")
    lim_req = groq_quota.get("limit_requests")
    res_tok = groq_quota.get("reset_tokens", "N/A")
    res_req = groq_quota.get("reset_requests", "N/A")
    
    tok_str = f"{int(rem_tok):,} / {int(lim_tok):,}" if rem_tok and lim_tok else f"{rem_tok} / {lim_tok}"
    req_str = f"{int(rem_req):,} / {int(lim_req):,}" if rem_req and lim_req else f"{rem_req} / {lim_req}"
    
    st.sidebar.metric("Elérhető Tokenek", tok_str, help=f"Reset idő: {res_tok}")
    st.sidebar.metric("Elérhető Kérések", req_str, help=f"Reset idő: {res_req}")
    st.sidebar.caption(f"Frissítve: {groq_quota.get('last_updated', 'Most')} | Modell: `{groq_client.model}`")
else:
    st.sidebar.warning("GROQ API offline (nincs beállítva a GROQ_API_KEY).")

# Statisztikai kártyák
stats = db.get_stats()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Összes Entitás", stats.get("entities", 0), help="Wikidata, Wikipédia és kurált entitások")
col2.metric("Gráf Relációk", stats.get("relations", 0), help="Irányított tudáskapcsolatok száma")
col3.metric("Kvízkérdések", stats.get("quiz_questions", 0), help="Korpusz és generált kérdések száma")
col4.metric("Kérdés-Entitás Kapcsolatok", stats.get("question_entities", 0))

st.markdown("---")

# 1. Modul: DuckDB & Gráf Böngésző
if menu == "📊 DuckDB & Gráf Böngésző":
    st.subheader("📁 DuckDB Adatbázis és Táblák")
    
    tab1, tab2 = st.tabs(["📋 Táblák Megtekintése", "💻 Egyéni SQL Konzol"])
    
    with tab1:
        table_name = st.selectbox(
            "Válaszd ki a megjelenítendő táblát:",
            ["entities", "relations", "quiz_questions", "entity_relevance", "question_entities"]
        )
        
        # Keresőmező
        search_term = st.text_input("🔍 Keresés a táblában (szöveg alapján):", "")
        
        query = f"SELECT * FROM {table_name}"
        if search_term:
            # entities esetén a label_hu-ra szűrünk
            if table_name == "entities":
                query += f" WHERE label_hu ILIKE '%{search_term}%' OR domain ILIKE '%{search_term}%'"
            elif table_name == "relations":
                query += f" WHERE relation_type ILIKE '%{search_term}%'"
            elif table_name == "quiz_questions":
                query += f" WHERE text ILIKE '%{search_term}%' OR correct_answer ILIKE '%{search_term}%'"
        
        query += " LIMIT 100"
        
        try:
            df = db.conn.execute(query).df()
            st.dataframe(df, width="stretch", height=400)
            st.caption(f"Megjelenítve legfeljebb 100 sor. Összesen a táblában: {stats.get(table_name, 0)} sor.")
        except Exception as e:
            st.error(f"Hiba a tábla beolvasásakor: {e}")

    with tab2:
        st.write("Futtass tetszőleges SQL lekérdezést a DuckDB felett:")
        sql_input = st.text_area(
            "SQL Lekérdezés:",
            "SELECT domain, COUNT(*) as darab FROM entities GROUP BY domain ORDER BY darab DESC;"
        )
        if st.button("▶️ Lekérdezés futtatása"):
            try:
                res_df = db.conn.execute(sql_input).df()
                st.dataframe(res_df, width="stretch")
            except Exception as e:
                st.error(f"SQL Hiba: {e}")

# 2. Modul: Kvíz Generátor & Játék
elif menu == "🎯 Kvíz Generátor & Játék":
    st.subheader("🎯 Automatikus Kérdésgenerálás & Interaktív Próba")
    
    c_gen1, c_gen2 = st.columns([1, 2])
    
    with c_gen1:
        st.markdown("#### Beállítások")
        selected_domain = st.selectbox(
            "Témakör:",
            ["bármely", "science_tech", "geography", "literature", "general"]
        )
        domain_enum = None if selected_domain == "bármely" else Domain(selected_domain)
        
        gen_btn = st.button("✨ Új Kérdés Generálása a Gráfból", type="primary")
    
    with c_gen2:
        if gen_btn:
            with st.spinner("Kérdés generálása folyamatban a Knowledge Graph tripletek és a Groq segítségével..."):
                gen = QuizGenerator(db)
                new_q = gen.generate_question(domain=domain_enum)
                if new_q:
                    st.session_state["current_question"] = new_q
                    st.success("Új kérdés sikeresen előállítva és elmentve a DuckDB-be!")
                else:
                    st.warning("Nem sikerült kérdést generálni a megadott témakörben.")
        
        # Kérdés megjelenítése, ha van a sessionben
        q = st.session_state.get("current_question")
        if q:
            st.info(f"**Téma:** {q.domain.value.upper()} | **Mechanizmus:** {q.mechanism.value.upper()}")
            st.markdown(f"### {q.text}")
            
            if q.mechanism == QuestionMechanism.ABCD and q.options:
                user_choice = st.radio("Válaszd ki a helyes választ:", q.options)
                if st.button("Válasz ellenőrzése"):
                    mech = ABCDMechanism()
                    is_ok, score, fb = mech.evaluate(user_choice, q.correct_answer)
                    if is_ok:
                        st.success(f"🎉 {fb} (Pontszám: {score})")
                    else:
                        st.error(f"❌ {fb} (Pontszám: {score})")
            
            elif q.mechanism == QuestionMechanism.ESTIMATION:
                est_val = st.number_input("Add meg a tippedet (számérték / évszám):", value=1900, step=1)
                if st.button("Becslés ellenőrzése"):
                    mech = EstimationMechanism()
                    is_ok, score, fb = mech.evaluate(est_val, q.correct_answer)
                    if is_ok:
                        st.success(f"🎯 {fb} (Pontszám: {score})")
                    else:
                        st.warning(f"⚠️ {fb} (Pontszám: {score})")
            
            st.caption(f"Érintett entitások: {', '.join(q.entities)}")
        else:
            st.write("Kattints a bal oldali **'Új Kérdés Generálása'** gombra egy éles kvízkérdés előállításához!")

# 3. Modul: Top Kvízrelevancia
elif menu == "🏆 Top Kvízrelevancia":
    st.subheader("🏆 Legmagasabb Magyar Kvízrelevanciájú Entitások")
    st.write("A korpuszban való előfordulás és a kapcsolati fokszám (Degree Centrality) alapján számított fontossági pontszámok:")
    
    rel_engine = RelevanceEngine(db)
    top_entities = rel_engine.get_top_entities(limit=25)
    
    if top_entities:
        df_top = pd.DataFrame(top_entities)
        df_top.columns = ["Entitás ID", "Megnevezés", "Téma", "Altéma", "Kvíz Gyakoriság", "Kapcsolatok", "Relevancia Pont"]
        st.dataframe(df_top, width="stretch")
    else:
        st.info("Nincs még kiszámított relevancia. Futtasd a `python src/quizforge/cli/main.py calc-relevance` parancsot!")

# 4. Modul: Játékos & Kalibráció (Hamarosan)
elif menu == "👤 Játékos & Kalibráció (Hamarosan)":
    st.subheader("👤 Játékos Profil & Önértékelési Kalibráció (4. Fázis)")
    st.write("Ez a modul a következő fázisban valósul meg:")
    st.markdown("""
    * **Confidence Calibration Görbék:** A játékos magabiztossága ($0\% - 100\%$) a tényleges helyességgel összevetve.
    * **Brier Score:** Egzakt matematikai önértékelési pontosságmérés.
    * **Domain × Mechanism Képességmátrix:** Hol vannak az erősségek és a rejtett gyengeségek?
    """)
