"""QuizForge - Streamlit Vizuális Felület és DuckDB Tudásgráf Böngésző."""

import sys
from pathlib import Path

# src hozzáadása az importokhoz
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import pandas as pd
import time
import altair as alt

import importlib
import quizforge.core.constants
importlib.reload(quizforge.core.constants)

from quizforge.core.constants import (
    Domain, QuestionMechanism,
    get_domain_label, get_mechanism_label, get_category_label
)
from quizforge.storage.db import DatabaseManager
from quizforge.knowledge.relevance import RelevanceEngine
from quizforge.knowledge.bank_expander import expand_database_bank
from quizforge.quiz_engine.generator import QuizGenerator
from quizforge.quiz_engine.mechanisms.abcd import ABCDMechanism
from quizforge.quiz_engine.mechanisms.estimation import EstimationMechanism
from quizforge.player.repository import PlayerRepository
from quizforge.player.tracker import PlayerTracker
from quizforge.player.calibration import CalibrationEngine
from quizforge.optimizer.landscape import QuizLandscapeEngine
from quizforge.optimizer.targeted import TargetedLearningEngine

# Oldalbeállítások
st.set_page_config(
    page_title="QuizForge - Knowledge Graph & Kvíz Felkészítő",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. KÖVETELMÉNY: Teljes fehér háttér és magas kontrasztú, tökéletesen olvasható szövegek
st.markdown("""
<style>
    /* Fő felület: tiszta fehér háttér és sötét betűk */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    /* Tipográfia kényszerítése sötét, kontrasztos színekre */
    h1, h2, h3, h4, h5, h6, p, label, div {
        color: #0F172A !important;
    }
    .stCaption, caption {
        color: #475569 !important;
    }
    
    /* Metrika kártyák világos stílusban */
    [data-testid="stMetric"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stMetricValue"] {
        color: #1E40AF !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    
    /* Táblázatok keretezése */
    .stDataFrame {
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
    }
    
    /* Kvízkérdés Prémium Kártya (Világos háttér, kék szegély, sötét szöveg) */
    .quiz-card {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-left: 6px solid #2563EB;
        border-radius: 10px;
        padding: 22px 24px;
        margin-bottom: 24px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .quiz-card-badge {
        color: #2563EB !important;
        font-size: 0.85em;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .quiz-card-text {
        color: #0F172A !important;
        font-size: 1.35em !important;
        font-weight: 600 !important;
        margin-top: 10px !important;
        line-height: 1.45 !important;
        white-space: pre-line;
    }
    
    /* Vakfolt radar kártyák */
    .radar-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 4px solid #EF4444;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# Adatbázis elérése cache-elt kapcsolatkezelővel
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Fejléc
st.title("⚡ QuizForge – Knowledge Graph & Kvíz Platform")
st.caption("Adatvezérelt kvízfelkészítő rendszer magyar tudásgráf, kvíz-tájképek és Groq LLM integrációval")

# Oldalsáv
st.sidebar.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/database.svg", width=50)
st.sidebar.title("Navigáció")
menu = st.sidebar.radio(
    "Válassz modult:",
    [
        "📊 DuckDB & Gráf Böngésző",
        "🎯 Kvíz Gyakorló & Játék",
        "🧭 Kvíz Tájképek & Célzott Edzés",
        "👤 Játékos Profil & Kalibráció",
        "🏆 Top Kvízrelevancia",
    ]
)

# Offline Kérdésbank Bővítés Gomb
st.sidebar.markdown("---")
st.sidebar.subheader("📚 Offline Kérdésbank (0 Token)")
if st.sidebar.button("⚡ Bank Bővítése / Frissítése", use_container_width=True):
    with st.spinner("Offline kurált kérdések frissítése és Parquet szinkronizáció..."):
        added = expand_database_bank(db)
        try:
            db.load_from_parquet()
        except Exception:
            pass
        st.sidebar.success(f"{added} új kérdés szinkronizálva!")
        st.rerun()

# Groq API Valós idejű Token Figyelő az oldalsávban (Kímélő gyorsítótárazással)
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Groq API Kvóta Figyelő")
from quizforge.llm.groq_client import GroqClient

@st.cache_resource
def get_groq_client():
    return GroqClient()

groq_client = get_groq_client()

if groq_client.is_available:
    refresh_clicked = st.sidebar.button("🔄 Kvóta Frissítése", use_container_width=True)
    
    if refresh_clicked or "cached_groq_quota" not in st.session_state:
        st.session_state["cached_groq_quota"] = groq_client.get_quota_status(force_refresh=True)
    
    groq_quota = st.session_state["cached_groq_quota"]
    
    rem_tok = groq_quota.get("remaining_tokens")
    lim_tok = groq_quota.get("limit_tokens")
    rem_req = groq_quota.get("remaining_requests")
    lim_req = groq_quota.get("limit_requests")
    res_tok = groq_quota.get("reset_tokens", "N/A")
    res_req = groq_quota.get("reset_requests", "N/A")
    
    tok_str = f"{int(rem_tok):,} / {int(lim_tok):,}" if rem_tok and lim_tok else f"{rem_tok} / {lim_tok}"
    req_str = f"{int(rem_req):,} / {int(lim_req):,}" if rem_req and lim_req else f"{rem_req} / {lim_req}"
    
    st.sidebar.metric("Elérhető Tokenek", tok_str, help=f"Token bucket újratöltési idő: {res_tok}")
    st.sidebar.metric("Elérhető Kérések (Naponta)", req_str, help=f"Napi kéréskeret teljes resetje: {res_req}")
    st.sidebar.caption(f"Frissítve: {groq_quota.get('last_updated', 'Most')} | Modell: `{groq_client.model}`")
else:
    st.sidebar.warning("GROQ API offline (nincs beállítva a GROQ_API_KEY).")

# Statisztikai kártyák
stats = db.get_stats()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Összes Entitás", stats.get("entities", 0), help="Wikidata, Wikipédia és kurált entitások")
col2.metric("Gráf Relációk", stats.get("relations", 0), help="Irányított tudáskapcsolatok száma")
col3.metric("Kvízkérdések", stats.get("quiz_questions", 0), help="Korpusz és kurált kérdések száma")
col4.metric("Kérdés-Entitás Kapcsolatok", stats.get("question_entities", 0))

st.markdown("---")

# 1. Modul: DuckDB & Gráf Böngésző
if menu == "📊 DuckDB & Gráf Böngésző":
    st.subheader("📁 DuckDB Adatbázis és Táblák")
    
    tab1, tab2 = st.tabs(["📋 Táblák Megtekintése", "💻 Egyéni SQL Konzol"])
    
    with tab1:
        table_name = st.selectbox(
            "Válaszd ki a megjelenítendő táblát:",
            ["entities", "relations", "quiz_questions", "entity_relevance", "question_entities", "users", "player_answers", "player_skills"]
        )
        
        search_term = st.text_input("🔍 Keresés a táblában (szöveg alapján):", "")
        
        query = f"SELECT * FROM {table_name}"
        if search_term:
            if table_name == "entities":
                query += f" WHERE label_hu ILIKE '%{search_term}%' OR domain ILIKE '%{search_term}%'"
            elif table_name == "relations":
                query += f" WHERE relation_type ILIKE '%{search_term}%'"
            elif table_name == "quiz_questions":
                query += f" WHERE text ILIKE '%{search_term}%' OR correct_answer ILIKE '%{search_term}%'"
        
        query += " LIMIT 100"
        
        try:
            df = db.conn.execute(query).df().copy()
            # Magyarosítás a táblázatban is, ha releváns oszlopok vannak
            if "domain" in df.columns:
                df["domain"] = df["domain"].apply(get_domain_label)
            if "mechanism" in df.columns:
                df["mechanism"] = df["mechanism"].apply(get_mechanism_label)
            st.dataframe(df, width="stretch", height=400)
            st.caption(f"Megjelenítve legfeljebb 100 sor. Összesen a táblában: {stats.get(table_name, 0)} sor.")
        except Exception as e:
            st.error(f"Hiba a tábla beolvasásakor: {e}")

    with tab2:
        st.write("Futtass tetszőleges SQL lekérdezést a DuckDB felett:")
        sql_input = st.text_area(
            "SQL Lekérdezés:",
            "SELECT domain, mechanism, COUNT(*) as darab FROM quiz_questions GROUP BY domain, mechanism ORDER BY darab DESC;"
        )
        if st.button("▶️ Lekérdezés futtatása"):
            try:
                res_df = db.conn.execute(sql_input).df().copy()
                if "domain" in res_df.columns:
                    res_df["domain"] = res_df["domain"].apply(get_domain_label)
                if "mechanism" in res_df.columns:
                    res_df["mechanism"] = res_df["mechanism"].apply(get_mechanism_label)
                st.dataframe(res_df, width="stretch")
            except Exception as e:
                st.error(f"SQL Hiba: {e}")

# 2. Modul: Kvíz Gyakorló & Játék
elif menu == "🎯 Kvíz Gyakorló & Játék":
    st.subheader("🎯 Kvíz Gyakorló & Önértékelési Játék")
    st.caption("Gyakorolj valós kocsmakvíz kérdéseken, add meg a magabiztosságodat és kövesd nyomon a Brier pontszámodat!")

    player_repo = PlayerRepository(db)
    tracker = PlayerTracker(db)

    # Aktív játékos kiválasztása
    users_list = player_repo.list_users()
    user_names = [u["username"] for u in users_list]
    if "Teszt Elek" not in user_names:
        user_names.insert(0, "Teszt Elek")

    col_u1, col_u2 = st.columns([2, 1])
    with col_u1:
        current_name = st.session_state.get("active_user_name", "Teszt Elek")
        default_u_idx = user_names.index(current_name) if current_name in user_names else 0
        chosen_user = st.selectbox("👤 Játékos profil:", user_names, index=default_u_idx)
    with col_u2:
        new_name = st.text_input("Vagy új játékos:", placeholder="Új név...")
        if new_name and st.button("Hozzáadás"):
            chosen_user = new_name

    active_user = player_repo.get_or_create_user(chosen_user)
    user_id = active_user["user_id"]
    st.session_state["active_user_name"] = active_user["username"]

    # Célzott edzés állapotjelző
    targeted_queue = st.session_state.get("targeted_queue", [])
    targeted_quiz_name = st.session_state.get("targeted_quiz_name", "")
    if targeted_queue:
        st.info(f"🎯 **Célzott Edzés Folyamatban:** {targeted_quiz_name} ({len(targeted_queue)} kérdés maradt a sorban).")

    st.markdown("---")

    # Kérdésvezérlő sáv (szép magyar témamegnevezésekkel)
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.5, 1.5, 1])
    with c_ctrl1:
        domain_choices = ["bármely"] + [d.value for d in Domain]
        selected_domain = st.selectbox(
            "Témakör kiválasztása:",
            domain_choices,
            format_func=lambda x: "🌐 Összes témakör (Vegyes)" if x == "bármely" else get_domain_label(x)
        )
        domain_enum = None if selected_domain == "bármely" else Domain(selected_domain)
    
    with c_ctrl2:
        source_mode = st.radio("Kérdés forrása:", ["📚 Tárolt kvízbankból (0 token)", "✨ Új generálása a gráfból (Groq)"], horizontal=True)

    with c_ctrl3:
        st.write("")
        st.write("")
        fetch_btn = st.button("🎲 Következő Kérdés", type="primary", use_container_width=True)

    # Kérdés betöltése
    if fetch_btn or "current_question" not in st.session_state:
        st.session_state["last_eval_result"] = None
        st.session_state["question_start_time"] = time.time()
        
        if targeted_queue:
            next_q = targeted_queue.pop(0)
            st.session_state["current_question"] = next_q
            st.session_state["targeted_queue"] = targeted_queue
        elif "Új generálása" in source_mode:
            with st.spinner("Kérdés megfogalmazása a Tudásgráf és a Groq LLM segítségével..."):
                gen = QuizGenerator(db)
                st.session_state["current_question"] = gen.generate_question(domain=domain_enum)
        else:
            q_query = "SELECT question_id FROM quiz_questions"
            params = []
            if domain_enum:
                q_query += " WHERE domain = ?"
                params.append(domain_enum.value)
            q_query += " ORDER BY RANDOM() LIMIT 1"
            q_row = db.conn.execute(q_query, params).fetchone()
            if q_row:
                st.session_state["current_question"] = tracker.q_repo.get_by_id(q_row[0])
            else:
                st.session_state["current_question"] = None

    q = st.session_state.get("current_question")
    if not q:
        st.info("Nincs megjeleníthető kérdés a kiválasztott szűrőkkel. Kattints a 'Következő Kérdés' gombra!")
    else:
        # Kérdéskártya (Világos dizájn, tökéletes olvashatóság)
        dom_label = get_domain_label(q.domain)
        mech_label = get_mechanism_label(q.mechanism)
        sub_str = f" | ALTÉMA: {q.subdomain.title()}" if q.subdomain else ""

        st.markdown(f"""
        <div class="quiz-card">
            <span class="quiz-card-badge">
                TÉMA: {dom_label.upper()}{sub_str.upper()} &bull; TÍPUS: {mech_label.upper()}
            </span>
            <div class="quiz-card-text">{q.text}</div>
        </div>
        """, unsafe_allow_html=True)

        # Válaszadási űrlap mechanizmus-specifikusan (NEM minden ABCD!)
        user_answer = None

        if q.mechanism == QuestionMechanism.MISSING_LETTERS:
            st.markdown("##### ✍️ Betűkiegészítés:")
            user_answer = st.text_input(
                "Írd be a kiegészített teljes címet vagy közmondást:",
                placeholder="Pl. Volt egyszer egy vadnyugat / Pénz beszél, kutya ugat...",
                key=f"ans_{q.question_id}"
            )
            if q.options and len(q.options) > 1:
                with st.expander("💡 Segítség / Válaszlehetőségek megtekintése"):
                    st.caption(f"Opciók a segítséghez: {', '.join(q.options)}")

        elif q.mechanism == QuestionMechanism.DEDUCTION:
            st.markdown("##### 🕵️ Sztori / Dedukció:")
            user_answer = st.text_input(
                "Melyik mű vagy alkotás cselekményét rejti a fenti leírás? Írd be a címet:",
                placeholder="Pl. Tüskevár / Egri csillagok / A nagy Gatsby...",
                key=f"ans_{q.question_id}"
            )
            if q.options and len(q.options) > 1:
                with st.expander("💡 Segítség / Műcím opciók megtekintése"):
                    st.caption(f"Lehetséges művek: {', '.join(q.options)}")

        elif q.mechanism == QuestionMechanism.TRUE_FALSE:
            st.markdown("##### ⚖️ Igaz vagy Hamis?")
            user_answer = st.radio(
                "Döntsd el a fenti állításról:",
                ["Igaz", "Hamis"],
                horizontal=True,
                key=f"ans_{q.question_id}"
            )

        elif q.mechanism == QuestionMechanism.ESTIMATION:
            unit_label = q.metadata.get("unit", "") if q.metadata else ""
            tol = q.metadata.get("tolerance_percentage", 15.0) if q.metadata else 15.0
            hint = f" ({unit_label})" if unit_label else ""
            st.markdown(f"##### 🔢 Számérték Saccolás / Becslés {hint}:")
            user_answer = st.number_input(
                f"Add meg a tippet (elfogadási hibasáv kb. ±{int(tol)}%):",
                value=0,
                step=1,
                key=f"ans_{q.question_id}"
            )

        elif q.mechanism == QuestionMechanism.CONNECTION:
            st.markdown("##### 🔗 Kapcsolat / Mi a közös bennük?")
            user_answer = st.text_input(
                "Írd be a közös tulajdonságot vagy a kakukktojást magyarázattal:",
                placeholder="Pl. Mindannyian magyar Nobel-díjasok...",
                key=f"ans_{q.question_id}"
            )

        elif q.mechanism == QuestionMechanism.ORDERING:
            st.markdown("##### 🔀 Sorrendbe állítás:")
            if q.options and len(q.options) > 1:
                user_answer = st.radio("Válaszd ki a helyes sorrendet:", q.options, key=f"ans_{q.question_id}")
            else:
                user_answer = st.text_input(
                    "Add meg a helyes sorrendet (pl. B -> D -> A -> C vagy B, D, A, C):",
                    key=f"ans_{q.question_id}"
                )

        elif q.mechanism == QuestionMechanism.MATCHING:
            st.markdown("##### 🧩 Elemek Párosítása:")
            st.caption("Párosítsd össze a bal oldali fogalmakat a megfelelő jobb oldali párjukkal a lenyíló listákból!")

            pairs = {}
            if q.metadata and "pairs" in q.metadata and isinstance(q.metadata["pairs"], dict):
                pairs = q.metadata["pairs"]
            elif ":" in str(q.correct_answer):
                for part in str(q.correct_answer).split(","):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        pairs[k.strip()] = v.strip()

            left_items = list(pairs.keys()) if pairs else (q.options if q.options else [])
            right_items = list(pairs.values()) if pairs else []
            if not right_items and ":" in str(q.correct_answer):
                right_items = [v.strip() for k, v in pairs.items()]

            # Kevert jobb oldali lehetőségek
            sorted_right_options = sorted(list(set(right_items)))

            user_pair_dict = {}
            st.markdown("""
            <div style="background-color: #F8FAFC; padding: 14px 18px; border-radius: 8px; border: 1px solid #CBD5E1; margin-bottom: 12px;">
            """, unsafe_allow_html=True)
            for idx, left_val in enumerate(left_items):
                col_m1, col_m2 = st.columns([1.2, 1.8])
                with col_m1:
                    st.markdown(f"<div style='padding-top: 8px; font-weight: 600; color: #0F172A;'>{left_val} &rarr;</div>", unsafe_allow_html=True)
                with col_m2:
                    selected_match = st.selectbox(
                        f"Pár kiválasztása ({left_val})",
                        options=["(Válassz párt...)"] + sorted_right_options,
                        label_visibility="collapsed",
                        key=f"match_{q.question_id}_{idx}"
                    )
                    if selected_match != "(Válassz párt...)":
                        user_pair_dict[left_val] = selected_match
            st.markdown("</div>", unsafe_allow_html=True)

            user_answer = user_pair_dict

        elif q.options and len(q.options) > 1:
            # Klasszikus ABCD vagy Kezdőbetűs 4-választós
            st.markdown("##### 🔠 Válaszlehetőségek (ABCD):")
            user_answer = st.radio("Válaszd ki a helyes megoldást:", q.options, key=f"ans_{q.question_id}")

        else:
            user_answer = st.text_input("Írd be a válaszodat:", key=f"ans_{q.question_id}")

        st.markdown("#### 🤔 Önértékelés / Magabiztosság (Confidence)")
        confidence_pct = st.slider(
            "Mennyire vagy biztos benne, hogy helyes a válaszod?",
            min_value=0,
            max_value=100,
            value=75,
            step=5,
            format="%d%%",
            help="0%: Csak vakon tippeltem | 50%: Bizonytalan vagyok | 80%: Elég biztos | 100%: Halálbiztos pont"
        )
        conf_float = confidence_pct / 100.0

        c_sub1, c_sub2 = st.columns([1, 3])
        with c_sub1:
            submit_btn = st.button("🚀 Válasz Beküldése", type="primary", use_container_width=True)

        if submit_btn:
            elapsed_ms = int((time.time() - st.session_state.get("question_start_time", time.time())) * 1000)
            res = tracker.evaluate_and_record_answer(
                user_id=user_id,
                question_id=q.question_id,
                given_answer=user_answer,
                confidence_level=conf_float,
                response_time_ms=elapsed_ms
            )
            st.session_state["last_eval_result"] = res

        # Értékelés és visszajelzés
        eval_res = st.session_state.get("last_eval_result")
        if eval_res:
            st.markdown("---")
            if eval_res["is_correct"]:
                st.success(f"🎉 **HELYES VÁLASZ!** {eval_res['feedback']} (Pontszám: {eval_res['score']})")
            else:
                st.error(f"❌ **HELYTELEN!** {eval_res['feedback']} (A helyes válasz: **{eval_res['correct_answer']}**)")

            given_conf = eval_res["confidence_level"]
            was_ok = eval_res["is_correct"]
            if was_ok and given_conf >= 0.8:
                st.info(f"🎯 **Kiváló önismeret!** Magabiztos voltál ({int(given_conf*100)}%), és a válaszod valóban helyes.")
            elif not was_ok and given_conf >= 0.8:
                st.warning(f"⚠️ **Túlzott önbizalom (Overconfidence)!** Nagyon magabiztos voltál ({int(given_conf*100)}%), de a válasz téves. Kocsmakvízben ez veszélyes csapda!")
            elif was_ok and given_conf <= 0.4:
                st.info(f"💡 **Kishitűség (Underconfidence)!** Csak {int(given_conf*100)}%-ot adtál rá, pedig tudtad! Merj bátrabb lenni!")
            else:
                st.caption(f"Önértékelés rögzítve: {int(given_conf*100)}% magabiztosság.")

            k1, k2, k3 = st.columns(3)
            k1.metric("Összes Megválaszolt", f"{eval_res['total_answers']} db")
            bs_val = eval_res['brier_score']
            k2.metric("Aktuális Brier Score", f"{bs_val:.4f}" if bs_val is not None else "N/A", help="0.00 = tökéletes jóslás")
            k3.metric("Kalibráció Státusza", eval_res['bias_info']['label'].split()[0])

# 3. Modul: Kvíz Tájképek & Célzott Edzés
elif menu == "🧭 Kvíz Tájképek & Célzott Edzés":
    st.subheader("🧭 Kvíz Tájképek & Célzott Felkészülés (Targeted Training)")
    st.caption("A hazai kvízestek és kvízjátékok egyedi ujjlenyomata alapján optimalizált felkészülés a személyes vakfoltjaid felszámolására.")

    landscape_engine = QuizLandscapeEngine()
    profiles = landscape_engine.list_profiles()
    profile_map = {p.profile_id: p for p in profiles}

    profile_display_names = {
        "csomor": "🍺 Csömöri Kvízest (Általános, filmek, sport, földrajz)",
        "quizkrumpli": "🥔 QuizKrumpli (55 kérdés, 8 blokk, változatos mechanizmusok)",
        "quizland": "🗺️ Quizland (Sorrend, kapcsolat, igaz-hamis, pontlépcső)",
        "kertvarosi": "🏡 Kertvárosi Kvízjáték (Saccolások, rekordok, cukortartalom)",
        "inquizitor": "🕵️ Inquizitor Társasjáték (Sztori, saccolás ±30%, szófordítás, betűkiegészítés)",
        "honfoglalo": "🏰 Honfoglaló / Triviador (10 klasszikus téma, ABCD és becslések)"
    }

    c_prof1, c_prof2 = st.columns([1.5, 1])
    with c_prof1:
        chosen_p_id = st.selectbox(
            "Válassz célzott kvízestet vagy társasjátékot:",
            list(profile_map.keys()),
            format_func=lambda x: profile_display_names.get(x, x)
        )
        profile = profile_map[chosen_p_id]

    player_repo = PlayerRepository(db)
    users_list = player_repo.list_users()
    user_names = [u["username"] for u in users_list] or ["Teszt Elek"]
    with c_prof2:
        current_name = st.session_state.get("active_user_name", user_names[0])
        default_u_idx = user_names.index(current_name) if current_name in user_names else 0
        training_user = st.selectbox("Játékos:", user_names, index=default_u_idx)

    active_user = player_repo.get_or_create_user(training_user)
    user_id = active_user["user_id"]
    st.session_state["active_user_name"] = training_user

    # Profil részletező kártya
    st.markdown("---")
    c_pinfo1, c_pinfo2 = st.columns([1.2, 1])
    with c_pinfo1:
        cat_badge = get_category_label(profile.category)
        st.markdown(f"### {profile.name} (`{cat_badge}`)")
        st.markdown(f"**Leírás:** {profile.description}")
        if profile.rules_notes:
            st.info(f"💡 **Szabályok & Megjegyzés:** {profile.rules_notes}")

    with c_pinfo2:
        st.markdown("#### Kvíz Ujjlenyomat Súlyok")
        dom_items = sorted(profile.domain_weights.items(), key=lambda x: x[1], reverse=True)
        dom_df = pd.DataFrame([{"Témakör": get_domain_label(k), "Súlyarány": f"{v*100:.0f}%"} for k, v in dom_items])
        
        mech_items = sorted(profile.mechanism_weights.items(), key=lambda x: x[1], reverse=True)
        mech_df = pd.DataFrame([{"Kérdéstípus": get_mechanism_label(k), "Súlyarány": f"{v*100:.0f}%"} for k, v in mech_items])

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.write("**Fő témakörök:**")
            st.dataframe(dom_df, hide_index=True, use_container_width=True)
        with col_w2:
            st.write("**Mechanizmusok:**")
            st.dataframe(mech_df, hide_index=True, use_container_width=True)

    # Vakfolt Radar
    st.markdown("---")
    st.subheader(f"🎯 Vakfolt Radar: {training_user} esélyei a(z) {profile.name} kvízen")
    st.caption("A rendszer összeveti a játékos kalibrált készségmátrixát a verseny profiljával, és feltárja a legnagyobb pontvesztési kockázatokat.")

    opt_engine = TargetedLearningEngine(db)
    weak_spots = opt_engine.calculate_weak_spots(user_id, profile.profile_id, limit=4)

    if weak_spots:
        ws_cols = st.columns(len(weak_spots))
        for idx, ws in enumerate(weak_spots):
            with ws_cols[idx]:
                dom_hu = get_domain_label(ws['domain'])
                mech_hu = get_mechanism_label(ws['mechanism'])
                st.markdown(f"""
                <div class="radar-card">
                    <div style="font-size: 0.8em; color: #64748B; font-weight: bold;">#{idx+1} KOCKÁZAT</div>
                    <div style="font-weight: 700; font-size: 1.1em; color: #0F172A; margin: 6px 0;">{dom_hu}</div>
                    <div style="color: #DC2626; font-size: 0.88em; font-weight: 600;">{mech_hu}</div>
                    <hr style="margin: 8px 0; border: 0; border-top: 1px solid #E2E8F0;"/>
                    <div style="font-size: 0.85em; color: #334155;">Kvízsúly: <b>{ws['profile_weight']}</b></div>
                    <div style="font-size: 0.85em; color: #334155;">Jelenlegi szint: <b>{int(ws['current_skill']*100)}%</b></div>
                    <div style="font-size: 0.85em; color: #DC2626; font-weight: bold;">Kockázat: {ws['risk_score']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚡ Célzott Kérdéssor Generálása")
    c_btn1, c_btn2 = st.columns([1, 2])
    with c_btn1:
        gen_targeted_btn = st.button("🚀 Célzott Edzés Kérdéssor Betöltése", type="primary", use_container_width=True)

    if gen_targeted_btn or "targeted_display_qs" in st.session_state:
        if gen_targeted_btn:
            selected_qs = opt_engine.select_targeted_questions(user_id, profile.profile_id, count=6)
            st.session_state["targeted_display_qs"] = selected_qs
            st.session_state["targeted_queue"] = list(selected_qs)
            st.session_state["targeted_quiz_name"] = profile.name

        qs_to_show = st.session_state.get("targeted_display_qs", [])
        st.success(f"🎯 **{len(qs_to_show)} célzott kérdés előkészítve a(z) {profile.name} felkészüléshez!**")
        st.info("💡 A kérdések bekerültek a gyakorló sorba. A **'🎯 Kvíz Gyakorló & Játék'** fülön azonnal játszhatók!")

        with st.expander("👀 Kérdések megtekintése előre (Kvízmester nézet)", expanded=True):
            for i, tq in enumerate(qs_to_show, 1):
                tq_dom = get_domain_label(tq.domain)
                tq_mech = get_mechanism_label(tq.mechanism)
                st.markdown(f"**{i}. [{tq_dom} | {tq_mech}]** {tq.text}")
                if tq.options:
                    st.caption(f"Opciók: {', '.join(tq.options)}")
                st.markdown(f"**Helyes válasz:** `{tq.correct_answer}`")
                st.markdown("---")

# 4. Modul: Játékos Profil & Kalibráció
elif menu == "👤 Játékos Profil & Kalibráció":
    st.subheader("👤 Játékos Profil & Metakognitív Kalibráció")
    st.caption("A valós tudás és a magabiztosság egzakt matematikai mérése (Brier Score, Kalibrációs Görbék és Képességmátrix)")

    player_repo = PlayerRepository(db)
    tracker = PlayerTracker(db)

    users_list = player_repo.list_users()
    user_names = [u["username"] for u in users_list]
    if not user_names:
        user_names = ["Teszt Elek"]

    current_sel_name = st.session_state.get("active_user_name", "Teszt Elek")
    default_idx = user_names.index(current_sel_name) if current_sel_name in user_names else 0

    sel_player = st.selectbox("Válassz játékost a profil megtekintéséhez:", user_names, index=default_idx)
    user = player_repo.get_or_create_user(sel_player)
    profile = tracker.get_player_profile(user["user_id"])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Megválaszolt Kérdések", f"{profile['total_answers']} db")
    kpi2.metric("Találati Arány (Accuracy)", f"{profile['accuracy'] * 100:.1f}%")
    bs = profile["brier_score"]
    kpi3.metric("Brier Score", f"{bs:.4f}" if bs is not None else "N/A", help="0.00 = tökéletes metakogníció, 0.25 = véletlen találgatás")
    bias_data = profile["bias_info"]
    kpi4.metric("Kalibrációs Állapot", bias_data["type"].upper(), delta=f"{bias_data['bias']:+.2f} bias", delta_color="inverse")

    st.markdown(f"**Értékelés és tanács:** {bias_data['label']} – *{bias_data.get('advice', '')}*")
    st.markdown("---")

    if profile["total_answers"] == 0:
        st.info("Ez a játékos még nem válaszolt meg kérdéseket. Menj a **'🎯 Kvíz Gyakorló & Játék'** menüpontba kérdések megválaszolásához!")
    else:
        tab_prof1, tab_prof2, tab_prof3 = st.tabs(["📈 Kalibrációs Görbe", "🗺️ Képességmátrix (Domain × Mechanism)", "📜 Válasznapló"])

        with tab_prof1:
            st.markdown("#### Kalibrációs Diagram (Valós Pontosság vs. Bevallott Magabiztosság)")
            st.caption("Az ideális (tökéletesen kalibrált) játékos a szaggatott vonalon halad. A vonal alatti pontok túlzott önbizalmat (Overconfidence), a vonal felettiek kishitűséget (Underconfidence) jeleznek.")

            curve_data = profile["calibration_curve"]
            valid_points = [p for p in curve_data if p["accuracy"] is not None]

            if valid_points:
                chart_df = pd.DataFrame([
                    {"Magabiztosság": p["expected_prob"], "Pontosság": p["accuracy"], "Minták": p["sample_count"], "Sáv": p["bin_range"]}
                    for p in valid_points
                ])

                ref_df = pd.DataFrame({"Magabiztosság": [0.0, 1.0], "Pontosság": [0.0, 1.0]})
                ref_line = alt.Chart(ref_df).mark_line(strokeDash=[5, 5], color="#94A3B8").encode(
                    x=alt.X("Magabiztosság:Q", scale=alt.Scale(domain=[0, 1])),
                    y=alt.Y("Pontosság:Q", scale=alt.Scale(domain=[0, 1]))
                )

                player_line = alt.Chart(chart_df).mark_line(point=True, color="#2563EB").encode(
                    x=alt.X("Magabiztosság:Q", title="Átlagos Magabiztosság"),
                    y=alt.Y("Pontosság:Q", title="Tényleges Sikerességi Arány"),
                    tooltip=["Sáv", "Magabiztosság", "Pontosság", "Minták"]
                )

                full_chart = (ref_line + player_line).properties(width=700, height=400)
                st.altair_chart(full_chart, use_container_width=True)
            else:
                st.write("Még nincs elegendő sávos adat a görbe rajzolásához.")

        with tab_prof2:
            st.markdown("#### Képességmátrix (Témakör × Kérdéstípus)")
            st.write("Itt láthatod a témakörök és kérdéstípusok szerinti pontosságodat és torzításodat magyar címkékkel:")
            if profile["skill_matrix"]:
                sm_df = pd.DataFrame(profile["skill_matrix"]).copy()
                sm_df["domain"] = sm_df["domain"].apply(get_domain_label)
                sm_df["mechanism"] = sm_df["mechanism"].apply(get_mechanism_label)
                sm_df.columns = ["Témakör", "Kérdéstípus", "Mintaszám", "Pontosság", "Átl. Magabiztosság", "Brier Score", "Torzítás (Bias)"]
                st.dataframe(sm_df, width="stretch")
            else:
                st.write("Nincs még kitöltött képességmátrix.")

        with tab_prof3:
            st.markdown("#### Korábbi Válaszok Története")
            if profile["recent_answers"]:
                rec_df = pd.DataFrame(profile["recent_answers"])[
                    ["created_at", "domain", "mechanism", "question_text", "given_answer", "correct_answer", "is_correct", "confidence_level", "response_time_ms"]
                ].copy()
                rec_df["domain"] = rec_df["domain"].apply(get_domain_label)
                rec_df["mechanism"] = rec_df["mechanism"].apply(get_mechanism_label)
                rec_df.columns = ["Dátum", "Témakör", "Kérdéstípus", "Kérdés", "Adott Válasz", "Helyes Válasz", "Helyes?", "Bizonyosság", "Válaszidő (ms)"]
                st.dataframe(rec_df, width="stretch")
            else:
                st.write("Nincs rögzített válasz.")

# 5. Modul: Top Kvízrelevancia
elif menu == "🏆 Top Kvízrelevancia":
    st.subheader("🏆 Legmagasabb Magyar Kvízrelevanciájú Entitások")
    st.write("A korpuszban való előfordulás és a kapcsolati fokszám alapján számított fontossági pontszámok:")
    
    rel_engine = RelevanceEngine(db)
    top_entities = rel_engine.get_top_entities(limit=25)
    
    if top_entities:
        df_top = pd.DataFrame(top_entities).copy()
        if "domain" in df_top.columns:
            df_top["domain"] = df_top["domain"].apply(get_domain_label)
        df_top.columns = ["Entitás ID", "Megnevezés", "Témakör", "Altéma", "Kvíz Gyakoriság", "Kapcsolatok", "Relevancia Pont"]
        st.dataframe(df_top, width="stretch")
    else:
        st.info("Nincs még kiszámított relevancia. Futtasd a `python src/quizforge/cli/main.py calc-relevance` parancsot!")
