#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VitaSteps Hiking Companion – Logisztikai és Időzítési Tervező Motor
Kiszámolja a teljes otthontól-otthonig idővonalat valós GPX és BKK GTFS adatok alapján.
"""

import json
import os
from datetime import datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))

def load_data():
    with open(os.path.join(DIR, "trails.json"), "r", encoding="utf-8") as f:
        trails = {t["id"]: t for t in json.load(f)}
    with open(os.path.join(DIR, "schedules.json"), "r", encoding="utf-8") as f:
        schedules = json.load(f)
    return trails, schedules

def parse_time_to_minutes(time_str):
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(mins):
    mins = int(round(mins)) % (24 * 60)
    h = mins // 60
    m = mins % 60
    return f"{h:02d}:{m:02d}"

def find_next_departure(schedule_list, target_minutes, min_buffer=5):
    """Keresi a legközelebbi járatot, ami target_minutes + min_buffer után indul."""
    threshold = target_minutes + min_buffer
    sorted_sched = sorted([parse_time_to_minutes(t) for t in schedule_list])
    for dep in sorted_sched:
        if dep >= threshold:
            return dep
    # Ha aznap nincs több járat
    return sorted_sched[0] if sorted_sched else threshold

def find_best_departure_before(schedule_list, target_minutes):
    """Keresi a legkésőbbi járatot, ami target_minutes előtt indul."""
    sorted_sched = sorted([parse_time_to_minutes(t) for t in schedule_list])
    candidates = [d for d in sorted_sched if d <= target_minutes]
    return candidates[-1] if candidates else sorted_sched[0]

def plan_hiking_trip(trail_id, home_departure="07:30", transit_to_hub_min=25, pace_kmh=4.0, breaks_count=2, break_duration_min=15):
    trails, schedules = load_data()
    trail = trails.get(trail_id)
    if not trail:
        raise ValueError(f"Ismeretlen túra: {trail_id}")

    sched_to = schedules[trail["schedule_to_key"]]
    sched_from = schedules[trail["schedule_from_key"]]
    transit_duration = trail["transit_duration_min"]

    # 1. Odaút számítása
    home_dep_mins = parse_time_to_minutes(home_departure)
    hub_arrival_mins = home_dep_mins + transit_to_hub_min

    # Keressük az első járatot a csomópontról
    transit_dep_mins = find_next_departure(sched_to, hub_arrival_mins, min_buffer=5)
    hub_wait_mins = transit_dep_mins - hub_arrival_mins
    trail_start_mins = transit_dep_mins + transit_duration

    # 2. Túra időigényének számítása (Energy Kilometers képlet alapján)
    # EK = D + (Elevation / 95)
    energy_km = trail["energy_km"]
    
    # 3 forgatókönyv:
    # - Gyorsabb tempó: +15% sebesség
    # - Normál tempó: megadott sétatempó
    # - Lassabb tempó: -15% sebesség
    scenarios = {}
    total_break_time_min = breaks_count * break_duration_min

    for label, pace_factor, name in [
        ("faster", 1.15, "Gyorsabb haladás (+15% tempó)"),
        ("normal", 1.00, "Tervezett normál tempó"),
        ("slower", 0.85, "Kényelmesebb / lassabb (-15% tempó)")
    ]:
        eff_pace = pace_kmh * pace_factor
        walk_hours = energy_km / eff_pace
        walk_minutes = walk_hours * 60.0
        hike_total_minutes = walk_minutes + total_break_time_min

        trail_finish_mins = trail_start_mins + hike_total_minutes

        # Hazautazás: járatkeresés a túra célállomásáról
        # 10 perc pihenő/átállási puffer a busz/hév megállóig
        bus_dep_mins = find_next_departure(sched_from, trail_finish_mins, min_buffer=8)
        buffer_at_stop = bus_dep_mins - trail_finish_mins
        hub_return_mins = bus_dep_mins + transit_duration
        home_arrival_mins = hub_return_mins + transit_to_hub_min

        scenarios[label] = {
            "name": name,
            "pace_kmh": round(eff_pace, 2),
            "walk_duration_str": f"{int(walk_minutes // 60)}ó {int(round(walk_minutes % 60))}p",
            "total_hike_duration_str": f"{int(hike_total_minutes // 60)}ó {int(round(hike_total_minutes % 60))}p",
            "trail_finish_time": minutes_to_time_str(trail_finish_mins),
            "return_transit_dep": minutes_to_time_str(bus_dep_mins),
            "buffer_at_stop_min": int(round(buffer_at_stop)),
            "hub_return_time": minutes_to_time_str(hub_return_mins),
            "home_arrival_time": minutes_to_time_str(home_arrival_mins),
            "total_door_to_door_min": int(round(home_arrival_mins - home_dep_mins))
        }

    plan = {
        "trail": {
            "id": trail["id"],
            "name": trail["name"],
            "distance_km": trail["distance_km"],
            "elevation_gain_m": trail["elevation_gain_m"],
            "energy_km": trail["energy_km"],
            "transit_line": trail["transit_line"],
            "transit_hub": trail["transit_hub"],
            "start_stop": trail["start_stop"],
        },
        "parameters": {
            "home_departure": home_departure,
            "transit_to_hub_min": transit_to_hub_min,
            "base_pace_kmh": pace_kmh,
            "breaks_count": breaks_count,
            "break_duration_min": break_duration_min,
            "total_break_min": total_break_time_min
        },
        "outbound": {
            "home_departure": home_departure,
            "hub_arrival": minutes_to_time_str(hub_arrival_mins),
            "transit_departure": minutes_to_time_str(transit_dep_mins),
            "hub_wait_min": hub_wait_mins,
            "trail_arrival": minutes_to_time_str(trail_start_mins),
            "transit_line": trail["transit_line"]
        },
        "scenarios": scenarios
    }
    return plan

if __name__ == "__main__":
    p = plan_hiking_trip("kevely_klasszik", home_departure="08:00")
    print(json.dumps(p, indent=2, ensure_ascii=False))
