# visualize.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_goat_bar(goat_df: pd.DataFrame, top_n: int = 10):
    """
    GOAT-index Top N versenyző oszlopdiagram.
    """
    df = goat_df.head(top_n).copy()
    df['name'] = df['forename'] + ' ' + df['surname']

    fig = px.bar(
        df.sort_values('goat_index', ascending=True),
        x='goat_index',
        y='name',
        orientation='h',
        title=f'Top {top_n} GOAT Index',
        labels={'goat_index': 'GOAT Index', 'name': 'Driver'},
        height=600,
    )
    fig.update_layout(yaxis=dict(tickfont=dict(size=12)))
    return fig


def plot_goat_scatter(goat_df: pd.DataFrame):
    """
    Szórásdiagram: teammate_score vs win_rate
    """
    df = goat_df.copy()
    df['name'] = df['forename'] + ' ' + df['surname']

    fig = px.scatter(
        df,
        x='teammate_score',
        y='win_rate',
        size='goat_index',
        color='goat_index',
        hover_name='name',
        title='Teammate Score vs Win Rate',
        labels={
            'teammate_score': 'Teammate Score',
            'win_rate': 'Win Rate'
        },
        color_continuous_scale='Viridis'
    )
    return fig


def plot_driver_career(goat_df: pd.DataFrame, driver_id: int, results_df: pd.DataFrame, races_df: pd.DataFrame):
    """
    Egy versenyző szezononkénti pontszámainak alakulása (line chart).
    """
    df = results_df[results_df['driverId'] == driver_id].merge(
        races_df[['raceId', 'year']], on='raceId', how='left'
    )

    season_points = df.groupby('year')['normalized_points'].sum().reset_index()

    name_row = goat_df[goat_df['driverId'] == driver_id]
    if not name_row.empty:
        driver_name = f"{name_row.iloc[0]['forename']} {name_row.iloc[0]['surname']}"
    else:
        driver_name = f"Driver {driver_id}"

    fig = px.line(
        season_points,
        x='year',
        y='normalized_points',
        markers=True,
        title=f'{driver_name} – Season Points Over Time',
        labels={'normalized_points': 'Normalized Points', 'year': 'Year'},
    )
    return fig
