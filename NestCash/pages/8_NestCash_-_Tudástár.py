import streamlit as st

st.set_page_config(layout="wide")

# Oldal fejléc
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://i.ytimg.com/vi/vhl9wWLv2Yo/hqdefault.jpg", width=100)  # Ide jöhet a Tudástár ikon
with col2:
    st.title("Tudástár (szemléltető oldal, fejlesztés alatt...)")
    st.caption("Rövid, könnyen emészthető pénzügyi leckék - Mindennapi pénzügyi tudatosságért")

# Gamifikációs elemek
st.subheader("🏆 Saját tanulási statisztikáim")
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tanulási streak", "🔥 3 nap")
    with col2:
        st.metric("Teljesített leckék", "5/24")
    with col3:
        st.metric("Gyűjtött kitűzők", "2")

st.divider()

# Napi tanulási ajánlás
st.subheader("⏳ Tanulj ma is 5 perc alatt:")
with st.container(border=True):
    st.markdown("**Mi az a vésztartalék, és hogyan építsd fel?**")
    st.caption("2 perces lecke · Kezdő szint")
    if st.button("Tanulás megkezdése", key="daily_lesson"):
        st.session_state.current_lesson = "vésztartalék"

st.divider()

# Választó sáv a témakörök között
selected_category = st.radio(
    "Témakörök:",
    ["Pénzügyi alapok", "Költségkezelés", "Haladó tudás", "Pénzügyi önismeret"],
    horizontal=True
)

st.divider()

# Témakörönkénti leckék megjelenítése
st.subheader(f"{selected_category} leckék")

if selected_category == "Pénzügyi alapok":
    with st.expander("1. Mi fán terem a kamatos kamat?", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("2. Minek a vésztartalék, és miért építsd fel?", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("3. Jól költöd-e a fizetésed első napjától?", expanded=False):
        st.write("Fejlesztés alatt...")

elif selected_category == "Költségkezelés":
    with st.expander("1. Mi az a mentális könyvelés?", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("2. A leggyakoribb költési csapdák", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("3. Hogyan tervezz előre váratlan kiadásokra?", expanded=False):
        st.write("Fejlesztés alatt...")

elif selected_category == "Haladó tudás":
    with st.expander("1. Befektetések 101", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("2. Mikor érdemes hitelt felvenni - és mikor nem?", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("3. Infláció - miért számít neked is, és hogyan küszöböld ki?", expanded=False):
        st.write("Fejlesztés alatt...")

elif selected_category == "Pénzügyi önismeret":
    with st.expander("1. Miért vásárolunk impulzívan?", expanded=False):
        st.write("Fejlesztés alatt...")
    with st.expander("2. Hogyan ismerd fel a pénzügyi stresszt?", expanded=False):
        st.write("Fejlesztés alatt...")

# Lábléc
st.divider()
#st.caption("Tudástár v1.0 · Minden jog fenntartva · © 2024")
