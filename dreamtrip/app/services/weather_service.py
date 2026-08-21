import requests
from typing import Dict, Any, Tuple, Optional

def fetch_historical_climate(lat: float, lon: float, month: int) -> Tuple[float, float, float]:
    """
    Lekéri a célállomás koordinátáira a megadott hónap valós történelmi klímaadatait az Open-Meteo Archive API-ból.
    Visszatér: (temp_min, temp_max, avg_temp) Celsiusban.
    """
    # Érvényes reprezentatív év/időszak a klímaátlaghoz
    ref_year = 2025
    start_date = f"{ref_year}-{month:02d}-01"
    
    # Hónap utolsó napjának meghatározása
    if month in [1, 3, 5, 7, 8, 10, 12]:
        end_day = 31
    elif month in [4, 6, 9, 11]:
        end_day = 30
    else:
        end_day = 28
    end_date = f"{ref_year}-{month:02d}-{end_day:02d}"

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&"
        f"daily=temperature_2m_max,temperature_2m_min&timezone=GMT"
    )

    try:
        r = requests.get(url, timeout=4.5)
        if r.status_code == 200:
            data = r.json()
            max_temps = [t for t in data.get("daily", {}).get("temperature_2m_max", []) if t is not None]
            min_temps = [t for t in data.get("daily", {}).get("temperature_2m_min", []) if t is not None]
            
            if max_temps and min_temps:
                avg_max = sum(max_temps) / len(max_temps)
                avg_min = sum(min_temps) / len(min_temps)
                avg_temp = (avg_max + avg_min) / 2.0
                return round(avg_min, 1), round(avg_max, 1), round(avg_temp, 1)
    except Exception as e:
        print(f"  [WEATHER API WARN] Nem sikerült lekérni a valós időjárást ({lat}, {lon}): {e}")

    # Szezonális és szélességi kör alapú determinisztikus fallback
    lat_abs = abs(lat)
    is_summer_north = month in [6, 7, 8] and lat >= 0
    is_winter_north = month in [12, 1, 2] and lat >= 0
    
    if lat_abs < 25: # Trópusi
        fallback_avg = 27.0
    elif is_summer_north:
        fallback_avg = max(18.0, 32.0 - (lat_abs - 25) * 0.4)
    elif is_winter_north:
        fallback_avg = max(-5.0, 15.0 - (lat_abs - 25) * 0.6)
    else:
        fallback_avg = max(10.0, 22.0 - (lat_abs - 25) * 0.3)

    return round(fallback_avg - 4.0, 1), round(fallback_avg + 4.0, 1), round(fallback_avg, 1)

def calculate_weather_score(avg_temp: float, target_temp: float = 22.0) -> Tuple[float, str]:
    """
    Kiszámolja a normalizált időjárási pontszámot (0.0 - 1.0) a célhőmérséklethez képest.
    A pontszám szigorúan monoton: minél közelebb van a célhoz, annál magasabb.
    Max eltérés skála: 15°C (15°C eltérésnél score = 0).
    """
    diff = abs(avg_temp - target_temp)
    # Lineáris csillapítás: 1.0 - (diff / 15.0)
    score = max(0.0, min(1.0, 1.0 - (diff / 15.0)))
    
    if diff <= 2.0:
        desc = f"☀️ Ideális klíma ({avg_temp}°C, cél: {target_temp}°C)"
    elif diff <= 5.0:
        desc = f"🌤️ Kellemes hőmérséklet ({avg_temp}°C)"
    elif avg_temp > target_temp:
        desc = f"🔥 Melegebb az ideálisnál ({avg_temp}°C)"
    else:
        desc = f"❄️ Hűvösebb az ideálisnál ({avg_temp}°C)"
        
    return round(score, 3), desc
