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
    st.write("Loaded keys from data:", list(data.keys()))


    results_norm = apply_normalized_points(data['results'])
    driver_metrics = calculate_driver_metrics(results_norm, data['qualifying'])
    teammate_df = compare_teammates(results_norm, data['races'])

    return data, results_norm, driver_metrics, teammate_df


def main():
    st.set_page_config(page_title="F1 GOAT Index", layout="wide")
    st.title("🏁 Formula 1 GOAT Index (1950-2024)")

    data, results_norm, driver_metrics, teammate_df = prepare_data()
    
    menu = st.sidebar.selectbox("**Navigation:**", [
        "🏆 Top GOAT Drivers",
        "📊 Metric Correlations",
        "🚀 Driver Career Overview",
        "ℹ️ About"
    ])
    
    # Sidebar: Weight sliders
    st.sidebar.header("GOAT Index Weights")
    w_points = st.sidebar.slider("Points weight", 0.0, 1.0, 0.15, 0.05)
    w_avg_points = st.sidebar.slider("Avg. Points weight", 0.0, 1.0, 0.20, 0.05)
    w_win = st.sidebar.slider("Win rate weight", 0.0, 1.0, 0.20, 0.05)
    w_pole = st.sidebar.slider("Pole rate weight", 0.0, 1.0, 0.10, 0.05)
    w_teammate = st.sidebar.slider("Teammate comparison weight", 0.0, 1.0, 0.35, 0.05)
    
    st.sidebar.markdown("### Filter Options")
    min_races = st.sidebar.slider("Minimum races required", 0, 300, 30, 5)
    
    total_w = w_points + w_avg_points + w_win + w_pole + w_teammate
    if total_w == 0:
        st.sidebar.error("Total weight cannot be zero!")
        return

    weights = {
        'points': w_points / total_w,
        'avg_points': w_avg_points / total_w,
        'win_rate': w_win / total_w,
        'pole_rate': w_pole / total_w,
        'teammate_score': w_teammate / total_w,
    }

    goat_df = calculate_goat_index(driver_metrics, teammate_df, weights=weights)

    drivers = data['drivers'][['driverId', 'forename', 'surname']]
    goat_df = goat_df.merge(drivers, on='driverId', how='left')

    

    if menu == "🏆 Top GOAT Drivers":
        top_drivers_df = goat_df.copy()
        top_drivers_df = top_drivers_df[top_drivers_df["races"] >= min_races]
        
        st.header("Top 10 Drivers by GOAT Index")
        fig = plot_goat_bar(top_drivers_df, top_n=10)
        st.plotly_chart(fig, use_container_width=True)

        # Show more metrics
        st.subheader("GOAT Metrics Table")
        top_drivers_df["name"] = top_drivers_df["forename"] + " " + top_drivers_df["surname"]
        metrics_cols = [
            "name", "races", "wins", "poles",
            "total_points", "avg_points",
            "win_rate", "pole_rate", "teammate_score",
            "goat_index"
        ]
        st.dataframe(
            top_drivers_df[metrics_cols].sort_values("goat_index", ascending=False).reset_index(drop=True),
            use_container_width=True
        )

        # Search box for driver
        st.subheader("🔍 Search for a Driver")
        driver_names = top_drivers_df["name"].sort_values().tolist()
        selected_driver_name = st.selectbox("Select a driver to view their metrics:", driver_names)

        if selected_driver_name:
            selected_row = top_drivers_df[top_drivers_df["name"] == selected_driver_name].iloc[0]
            st.markdown(f"### Stats for {selected_driver_name}")

            display_row = selected_row.copy()
            display_row["name"] = f"{selected_row['forename']} {selected_row['surname']}"
            display_row = display_row[[
                "name", "races", "wins", "poles", "total_points", "avg_points",
                "win_rate", "pole_rate", "teammate_score", "goat_index"
            ]]
            
            # Egy soros DataFrame-ként megjelenítés
            st.dataframe(display_row.to_frame().T)

            
    elif menu == "📊 Metric Correlations":
        st.header("Metric Correlation Analysis")
        fig = plot_goat_scatter(goat_df)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        This scatter plot shows the relationship between win rate and teammate performance.
        Each dot represents a driver, with the size and color indicating their GOAT index.
        """)

    elif menu == "🚀 Driver Career Overview":
        st.header("Driver Season-by-Season Performance")
        driver_options = goat_df.sort_values('goat_index', ascending=False)
        driver_map = {
            f"{row.forename} {row.surname}": row.driverId
            for _, row in driver_options.iterrows()
        }
        selected_driver = st.selectbox("Select a driver:", list(driver_map.keys()))

        if selected_driver:
            driver_id = driver_map[selected_driver]
            fig = plot_driver_career(goat_df, driver_id, results_norm, data['races'])
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "ℹ️ About":
        st.header("About this App")
        st.markdown("""
        This Streamlit application calculates and visualizes a **Formula 1 GOAT Index**,
        which evaluates all drivers across F1 history using normalized and contextual metrics.

        The GOAT Index combines:
        - Normalized points per race
        - Normalized total points
        - Win rate
        - Pole position rate
        - Teammate performance score

        All scores are weighted according to the sliders on the sidebar.
        You can explore different definitions of "greatest" by tuning these weights.
        """)

    else:
        st.write("Please select a section from the sidebar.")


if __name__ == "__main__":
    main()
