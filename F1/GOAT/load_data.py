# load_data.py

import pandas as pd
import os
import streamlit as st

def load_all_data(data_dir='datafiles'):
    """
    Betölti az összes F1 adatfájlt a megadott könyvtárból.
    
    Paraméterek:
        data_dir (str): Az adatfájlokat tartalmazó könyvtár neve.
    
    Visszatérés:
        dict: Egy szótár, amely minden fájlt tartalmaz DataFrame formátumban.
    """

    filenames = [
        'circuits.csv',
        'constructor_results.csv',
        'constructor_standings.csv',
        'constructors.csv',
        'driver_standings.csv',
        'drivers.csv',
        'lap_times.csv',
        'pit_stops.csv',
        'qualifying.csv',
        'races.csv',
        'results.csv',
        'seasons.csv',
        'sprint_results.csv',
        'status.csv',
    ]

    data = {}

    for file in filenames:
        name = file.replace('.csv', '')
        path = os.path.join(data_dir, file)

        try:
            df = pd.read_csv(path)
            data[name] = df
        except FileNotFoundError:
            st.error(f"[HIBA] Nem található adatfájl: {path}")
        except Exception as e:
            st.error(f"[HIBA] Nem sikerült betölteni: {path} -> {e}")

    # ----- Típus- és dátumkonverziók -----

    # Dátumformátum
    if 'races' in data:
        if 'date' in data['races'].columns:
            data['races']['date'] = pd.to_datetime(data['races']['date'], errors='coerce')

    if 'pit_stops' in data:
        data['pit_stops']['time'] = pd.to_datetime(data['pit_stops']['time'], errors='coerce')
        data['pit_stops']['milliseconds'] = pd.to_numeric(data['pit_stops']['milliseconds'], errors='coerce')

    if 'lap_times' in data:
        data['lap_times']['milliseconds'] = pd.to_numeric(data['lap_times']['milliseconds'], errors='coerce')

    if 'results' in data:
        data['results']['position'] = pd.to_numeric(data['results']['position'], errors='coerce')
        data['results']['points'] = pd.to_numeric(data['results']['points'], errors='coerce')

    if 'qualifying' in data:
        for col in ['q1', 'q2', 'q3']:
            if col in data['qualifying'].columns:
                data['qualifying'][col] = pd.to_timedelta(data['qualifying'][col], errors='coerce')

    return data