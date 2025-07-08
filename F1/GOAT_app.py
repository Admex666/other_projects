import streamlit as st
import pandas as pd

from GOAT.load_data import load_all_data
from GOAT.normalize_points import apply_normalized_points
from GOAT.metrics import calculate_driver_metrics
from GOAT.teammate_comparison import compare_teammates
from GOAT.goat_index import calculate_goat_index
from GOAT.visualize import plot_goat_bar, plot_goat_scatter, plot_driver_career


@st.cache_data(show_spinner=True)
def prepare_data(data_path='datafiles'):
    data = load_all_data(data_path)

    # Normalizált pontszámok
    results_norm = apply_normalized_points(data['results'])

    # Driver metrics (wins, poles, avg finish, races)
    driver_metrics = calculate_driver_metrics(results_norm, data['qualifying'])

    # Csapattárs összehasonlítás
    teammate_df = compare_teammates(results_norm, data['races'])

    # Driver neveket beillesztjük később a goat_df-be

    return data, results_norm, driver_metrics, teammate_df


def main():
    st.set_page_config(page_title="F1 GOAT Index Explorer", layout="wide")
    st.title("🏁 Formula-1 GOAT Index Explorer")

    # --- Betöltés (cache-elve) ---
    data, results_norm, driver_metrics, teammate_df = prepare_data()

    # --- Súlyok slider-ekkel a sidebar-ban ---
    st.sidebar.header("GOAT Index Súlyozás")
    w_points = st.sidebar.slider("Pontszám súlya", 0.0, 1.0, 0.30, 0.05)
    w_win = st.sidebar.slider("Győzelmi arány súlya", 0.0, 1.0, 0.25, 0.05)
    w_pole = st.sidebar.slider("Pole arány súlya", 0.0, 1.0, 0.15, 0.05)
    w_finish = st.sidebar.slider("Átlagos helyezés súlya", 0.0, 1.0, 0.15, 0.05)
    w_teammate = st.sidebar.slider("Csapattárs elleni teljesítmény súlya", 0.0, 1.0, 0.15, 0.05)

    # Súlyok normalizálása, hogy összegük 1 legyen, elkerülve hibát
    total_w = w_points + w_win + w_pole + w_finish + w_teammate
    if total_w == 0:
        st.sidebar.error("A súlyok összege nem lehet nulla!")
        return
    weights = {
        'points': w_points / total_w,
        'win_rate': w_win / total_w,
        'pole_rate': w_pole / total_w,
        'avg_finish': w_finish / total_w,
        'teammate_score': w_teammate / total_w,
    }

    # GOAT index újraszámolása
    goat_df = calculate_goat_index(driver_metrics, teammate_df, weights=weights)

    # Nevek betöltése és összevonása
    drivers = data['drivers'][['driverId', 'forename', 'surname']]
    goat_df = goat_df.merge(drivers, on='driverId', how='left')

    menu = st.sidebar.selectbox("Válassz menüpontot:", [
        "🏆 Top GOAT Pilóták",
        "📊 Teljesítmény Kapcsolatok",
        "🚀 Versenyző Karrierje",
        "ℹ️ Információ"
    ])

    if menu == "🏆 Top GOAT Pilóták":
        st.header("Top 10 GOAT Index versenyző")
        fig = plot_goat_bar(goat_df, top_n=10)
        st.plotly_chart(fig, use_container_width=True)

        st.write("**A GOAT Index a következő mutatók súlyozott kombinációja:**")
        st.markdown(f"""
        - Összesített normalizált pontszám (súly: {weights['points']:.2f})  
        - Győzelmi arány (súly: {weights['win_rate']:.2f})  
        - Pole pozíciók aránya (súly: {weights['pole_rate']:.2f})  
        - Átlagos befutóhelyezés (inverz, súly: {weights['avg_finish']:.2f})  
        - Csapattárs elleni teljesítmény (súly: {weights['teammate_score']:.2f})  
        """)

        st.dataframe(goat_df[['forename', 'surname', 'races', 'wins', 'poles', 'goat_index']].head(10))

    elif menu == "📊 Teljesítmény Kapcsolatok":
        st.header("Kapcsolatok a különböző mutatók között")
        fig = plot_goat_scatter(goat_df)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        Ez az ábra megmutatja, hogyan viszonyul a versenyzők csapattárs elleni teljesítménye (teammate score) és a győzelmi arányuk.
        A pontok mérete és színe a GOAT indexet jelzi.
        """)

    elif menu == "🚀 Versenyző Karrierje":
        st.header("Versenyző szezononkénti pontszámainak alakulása")
        driver_options = goat_df.sort_values('goat_index', ascending=False)
        driver_map = {
            f"{row.forename} {row.surname}": row.driverId
            for _, row in driver_options.iterrows()
        }
        selected_driver = st.selectbox("Válassz versenyzőt:", list(driver_map.keys()))

        if selected_driver:
            driver_id = driver_map[selected_driver]
            fig = plot_driver_career(goat_df, driver_id, results_norm, data['races'])
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "ℹ️ Információ":
        st.header("Információ")
        st.markdown("""
        Ez az alkalmazás egy **Formula-1 GOAT Index** számítást és vizualizációt valósít meg.

        **A GOAT Index** több mutató súlyozott kombinációja, amely normalizált pontszámokat, győzelmi arányt, pole pozíciókat, átlagos befutóhelyezést és csapattárs elleni teljesítményt vesz figyelembe.

        Az adatok az F1 teljes történelméből származnak.
        """)

    else:
        st.write("Válassz menüpontot a bal oldali menüből.")


if __name__ == "__main__":
    main()
