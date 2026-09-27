"""
Optivoya Shared Intelligence — Geo & Experience Intelligence Layer
===================================================================
Unified intelligence layer providing:
1. 12-Dimensional Experience Vector Cosine Similarity & Fit Scoring
   (Client preference matching vs Destination & POI profiles)
2. Opening Hours & Day-of-Week Schedule Validation
   (Google Places periods parsing, Monday/Tuesday closure detection, conflict alerts)
3. Geo-spatial Distance, Airport-to-Hotel Transit & POI Clustering Metrics
   (LocationScore calculation normalized to 0.0 - 10.0)
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# 1. 12-DIMENSIONAL EXPERIENCE VECTOR CONSTANTS & SYNONYM MAPPINGS
# ---------------------------------------------------------------------------

DIMENSIONS_12: List[str] = [
    "culture",
    "food",
    "beach",
    "nature",
    "nightlife",
    "romance",
    "authenticity",
    "locality",
    "walkability",
    "tourist_intensity",
    "adventure",
    "family",
]

# Canonical dimension alias mappings (User/Trip preferences -> 12D Vector Keys)
DIMENSION_ALIASES: Dict[str, str] = {
    # Culture / Heritage / Sightseeing
    "culture": "culture",
    "sightseeing": "culture",
    "history": "culture",
    "culture_history": "culture",
    "art": "culture",
    "museums": "culture",
    "heritage": "culture",
    # Food / Gastronomy
    "food": "food",
    "gastronomy": "food",
    "food_market": "food",
    "culinary": "food",
    "dining": "food",
    "wine": "food",
    # Beach / Coastal
    "beach": "beach",
    "beach_coastal": "beach",
    "coastal": "beach",
    "sea": "beach",
    "swimming": "beach",
    # Nature / Outdoors / Viewpoints
    "nature": "nature",
    "nature_viewpoint": "nature",
    "outdoors": "nature",
    "parks": "nature",
    "viewpoint": "nature",
    # Nightlife / Entertainment
    "nightlife": "nightlife",
    "nightlife_bar": "nightlife",
    "party": "nightlife",
    "bars": "nightlife",
    "clubs": "nightlife",
    # Romance / Relaxation / Wellness
    "romance": "romance",
    "relaxation": "romance",
    "wellness": "romance",
    "wellness_spa": "romance",
    "couples": "romance",
    # Authenticity
    "authenticity": "authenticity",
    "authentic": "authenticity",
    "hidden_gems": "authenticity",
    "local_character": "authenticity",
    # Locality / Shopping / Neighborhood
    "locality": "locality",
    "local_life": "locality",
    "shopping": "locality",
    "markets": "locality",
    "neighborhoods": "locality",
    # Walkability
    "walkability": "walkability",
    "walkable": "walkability",
    "pedestrian": "walkability",
    # Tourist intensity
    "tourist_intensity": "tourist_intensity",
    "popular": "tourist_intensity",
    "crowds": "tourist_intensity",
    # Adventure / Sports
    "adventure": "adventure",
    "active_adventure": "adventure",
    "sports": "adventure",
    "hiking": "adventure",
    "active": "adventure",
    # Family
    "family": "family",
    "family_kids": "family",
    "kids": "family",
    "children": "family",
}


# ---------------------------------------------------------------------------
# 2. EXPERIENCE VECTOR & COSINE SIMILARITY ENGINE
# ---------------------------------------------------------------------------

def normalize_preference_vector(
    preferences: Union[Dict[str, float], Any, List[str]],
    default_value: float = 50.0
) -> Dict[str, float]:
    """
    Converts diverse preference formats (Dict, ExperiencePreferences model, or list of interest tags)
    into a canonical 12-dimensional vector normalized to sum = 1.0 (unit L1 norm)
    or unit L2 norm for mathematical consistency.
    """
    raw_scores: Dict[str, float] = {d: 0.0 for d in DIMENSIONS_12}

    if hasattr(preferences, "dict") or hasattr(preferences, "__dict__"):
        p_dict = preferences.dict() if hasattr(preferences, "dict") else preferences.__dict__
        for k, v in p_dict.items():
            canonical_dim = DIMENSION_ALIASES.get(k.lower(), k.lower())
            if canonical_dim in raw_scores:
                raw_scores[canonical_dim] = max(raw_scores[canonical_dim], float(v or 0.0))
    elif isinstance(preferences, dict):
        for k, v in preferences.items():
            canonical_dim = DIMENSION_ALIASES.get(k.lower(), k.lower())
            if canonical_dim in raw_scores:
                raw_scores[canonical_dim] = max(raw_scores[canonical_dim], float(v or 0.0))
    elif isinstance(preferences, (list, tuple, set)):
        # List of interest tags e.g. ["culture", "gastronomy", "beach"]
        for tag in preferences:
            canonical_dim = DIMENSION_ALIASES.get(str(tag).lower(), str(tag).lower())
            if canonical_dim in raw_scores:
                raw_scores[canonical_dim] = 100.0

    # If all zeros, fallback to default uniform prior
    total = sum(raw_scores.values())
    if total <= 0:
        return {d: 1.0 / len(DIMENSIONS_12) for d in DIMENSIONS_12}

    return {d: val / total for d, val in raw_scores.items()}


def extract_destination_vector(dest_profile_or_vibe: Union[Dict[str, Any], Any]) -> Dict[str, float]:
    """
    Extracts the 12-dimensional absolute scores (0-100) from a destination experience profile
    or legacy vibe dictionary.
    """
    dest_vec: Dict[str, float] = {d: 50.0 for d in DIMENSIONS_12}

    if not dest_profile_or_vibe:
        return dest_vec

    if isinstance(dest_profile_or_vibe, dict):
        # 1. Check if experience_vector is nested
        exp_vec = dest_profile_or_vibe.get("experience_vector") or dest_profile_or_vibe.get("dimensions") or dest_profile_or_vibe
        if isinstance(exp_vec, dict) and "dimensions" in exp_vec:
            dims = exp_vec["dimensions"]
        elif isinstance(exp_vec, dict):
            dims = exp_vec
        else:
            dims = {}

        for k, v in dims.items():
            canonical_dim = DIMENSION_ALIASES.get(k.lower(), k.lower())
            if canonical_dim in dest_vec:
                if isinstance(v, dict):
                    dest_vec[canonical_dim] = float(v.get("absolute") or v.get("score") or 50.0)
                elif isinstance(v, (int, float)):
                    dest_vec[canonical_dim] = float(v)

        # 2. Check top level vibe scores if dimensions was empty
        for k in ["culture", "beach", "gastronomy", "food", "nightlife", "nature", "romance", "authenticity"]:
            if k in dest_profile_or_vibe:
                c_dim = DIMENSION_ALIASES.get(k, k)
                if c_dim in dest_vec:
                    dest_vec[c_dim] = float(dest_profile_or_vibe[k])

    return dest_vec


def calculate_cosine_similarity(
    vector_a: Dict[str, float],
    vector_b: Dict[str, float]
) -> float:
    """
    Computes mathematical cosine similarity between two 12-dimensional vectors.
    Result range: 0.0 to 1.0.
    Formula: cos(theta) = (A . B) / (||A|| * ||B||)
    """
    common_keys = set(vector_a.keys()) | set(vector_b.keys())
    if not common_keys:
        return 0.5

    dot_product = sum(float(vector_a.get(k, 0.0)) * float(vector_b.get(k, 0.0)) for k in common_keys)
    norm_a = math.sqrt(sum(float(vector_a.get(k, 0.0)) ** 2 for k in common_keys))
    norm_b = math.sqrt(sum(float(vector_b.get(k, 0.0)) ** 2 for k in common_keys))

    if norm_a == 0 or norm_b == 0:
        return 0.5

    sim = dot_product / (norm_a * norm_b)
    return max(0.0, min(1.0, float(sim)))


def calculate_experience_fit_12d(
    user_preferences: Union[Dict[str, float], Any, List[str]],
    destination_profile_or_vibe: Union[Dict[str, Any], Any]
) -> Dict[str, Any]:
    """
    Evaluates client-to-destination vibe compatibility across the 12 dimensions.
    Returns:
    - cosine_similarity: 0.0 - 1.0
    - fit_score_percent: 0.0 - 100.0 (weighted fit score)
    - top_matching_dimensions: Top 3 dimensions where user and destination align best
    - dimension_breakdown: Detailed per-dimension scores
    """
    u_vec = normalize_preference_vector(user_preferences)
    d_vec = extract_destination_vector(destination_profile_or_vibe)

    # Exclude tourist_intensity from positive fit calculation
    active_dims = [d for d in DIMENSIONS_12 if d != "tourist_intensity"]
    
    sub_u = {d: u_vec.get(d, 0.0) for d in active_dims}
    sub_d = {d: d_vec.get(d, 50.0) for d in active_dims}

    # Cosine similarity (evaluated on user's active dimensions for focused alignment)
    user_active_dims = [d for d in active_dims if sub_u.get(d, 0.0) > 0]
    if user_active_dims:
        active_u = {d: sub_u[d] for d in user_active_dims}
        active_d = {d: sub_d[d] for d in user_active_dims}
        cos_sim = calculate_cosine_similarity(active_u, active_d)
    else:
        cos_sim = calculate_cosine_similarity(sub_u, sub_d)

    # Weighted fit (0 - 100)
    weighted_sum = sum(sub_u[d] * sub_d[d] for d in active_dims)
    total_u_weight = sum(sub_u.values()) or 1.0
    weighted_fit_score = weighted_sum / total_u_weight

    # Identify alignment strength
    dimension_matches = []
    for d in active_dims:
        u_weight = sub_u.get(d, 0.0)
        d_val = sub_d.get(d, 50.0)
        match_score = (u_weight * 12.0) * (d_val / 100.0)
        dimension_matches.append((d, match_score, d_val, u_weight))

    dimension_matches.sort(key=lambda x: x[1], reverse=True)
    top_matches = [
        {"dimension": dm[0], "destination_score": round(dm[2], 1), "user_weight": round(dm[3], 3)}
        for dm in dimension_matches[:3]
    ]

    return {
        "cosine_similarity": round(cos_sim, 4),
        "fit_score_percent": round(max(10.0, min(100.0, weighted_fit_score)), 1),
        "normalized_score_0_1": round(max(0.1, min(1.0, weighted_fit_score / 100.0)), 3),
        "top_matching_dimensions": top_matches,
        "user_vector": {k: round(v, 3) for k, v in sub_u.items()},
        "destination_vector": {k: round(v, 1) for k, v in sub_d.items()},
    }


def calculate_activity_fit_score(
    activity: Dict[str, Any],
    user_preferences: Union[Dict[str, float], Any, List[str]]
) -> float:
    """
    Computes preference fit score (0.0 - 1.0) for an individual activity / POI.
    """
    u_vec = normalize_preference_vector(user_preferences)
    
    cat = str(activity.get("category") or activity.get("type") or "attraction").lower()
    subcat = str(activity.get("subcategory") or "").lower()
    tags = [t.lower() for t in (activity.get("tags") or [])]
    
    # Map activity to dimensions
    act_vec: Dict[str, float] = {d: 0.1 for d in DIMENSIONS_12}
    
    if "culture" in cat or "attraction" in cat or "museum" in cat or "church" in cat:
        act_vec["culture"] = 1.0
        act_vec["authenticity"] = 0.6
    if "food" in cat or "restaurant" in cat or "cafe" in cat or "gastronomy" in cat:
        act_vec["food"] = 1.0
        act_vec["locality"] = 0.7
    if "beach" in cat or "coastal" in cat:
        act_vec["beach"] = 1.0
        act_vec["nature"] = 0.5
    if "nature" in cat or "viewpoint" in cat or "park" in cat:
        act_vec["nature"] = 1.0
        act_vec["adventure"] = 0.5
    if "nightlife" in cat or "bar" in cat or "club" in cat:
        act_vec["nightlife"] = 1.0
    if "shopping" in cat or "market" in subcat:
        act_vec["locality"] = 0.8
    if "romantic" in tags or "viewpoint" in cat:
        act_vec["romance"] = 0.9
    if "family" in tags or "kids" in tags or "park" in cat:
        act_vec["family"] = 0.8

    rating = float(activity.get("rating") or 4.5)
    quality_mult = 0.7 + (rating / 5.0) * 0.3

    cos_sim = calculate_cosine_similarity(u_vec, act_vec)
    return round(float(cos_sim * quality_mult), 3)


# ---------------------------------------------------------------------------
# 3. OPENING HOURS & SCHEDULE VALIDATION ENGINE
# ---------------------------------------------------------------------------

DAY_NAMES_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_NAMES_HU = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]

def parse_time_string_hhmm(time_str: str) -> Tuple[int, int]:
    """Parses 'HH:MM' or 'HHMM' into (hour, minute)."""
    clean = time_str.replace(":", "").strip()
    if len(clean) == 4 and clean.isdigit():
        return int(clean[:2]), int(clean[2:])
    if ":" in time_str:
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
    return 9, 0


def is_poi_open_at_time(
    opening_hours: Optional[Dict[str, Any]],
    weekday_python: int,
    hour: int,
    minute: int
) -> bool:
    """
    Checks if a POI is open at a specific day and time.
    weekday_python: 0 (Monday) .. 6 (Sunday)
    hour: 0..23, minute: 0..59
    """
    if not opening_hours or not isinstance(opening_hours, dict):
        return True  # Open by default if no restrictive schedule declared

    periods = opening_hours.get("periods", [])
    if not periods:
        # Check weekday_text fallback if available
        weekday_text = opening_hours.get("weekday_text", [])
        if weekday_text and 0 <= weekday_python < len(DAY_NAMES_EN):
            day_name = DAY_NAMES_EN[weekday_python]
            for line in weekday_text:
                if line.startswith(day_name):
                    if "closed" in line.lower():
                        return False
        return True

    # Google Places day: 0=Sunday, 1=Monday, ..., 6=Saturday
    google_day = (weekday_python + 1) % 7
    current_time_num = hour * 100 + minute

    for period in periods:
        open_info = period.get("open", {})
        close_info = period.get("close", {})

        if not open_info:
            continue

        open_day = open_info.get("day")
        raw_open_time = open_info.get("time", "0000")
        try:
            open_time_num = int(raw_open_time)
        except ValueError:
            open_time_num = 0

        # 24-hour venue
        if open_day == google_day and raw_open_time == "0000" and not close_info:
            return True

        if open_day == google_day:
            if not close_info:
                return True
            close_day = close_info.get("day", google_day)
            raw_close_time = close_info.get("time", "2359")
            try:
                close_time_num = int(raw_close_time)
            except ValueError:
                close_time_num = 2359

            if close_day == google_day:
                if open_time_num <= current_time_num <= close_time_num:
                    return True
            else:
                # Spans into next morning (e.g. 18:00 to 02:00)
                if current_time_num >= open_time_num:
                    return True

        # Check if carried over from previous day
        prev_google_day = (google_day - 1) % 7
        if open_info.get("day") == prev_google_day and close_info:
            close_day = close_info.get("day")
            try:
                close_time_num = int(close_info.get("time", "0000"))
            except ValueError:
                close_time_num = 0
            if close_day == google_day and current_time_num <= close_time_num:
                return True

    return False


def get_closed_days_of_week(opening_hours: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes opening hours to detect recurring closed days (e.g. 'Closed on Mondays').
    Returns list of closed days with both English and Hungarian names.
    """
    if not opening_hours or not isinstance(opening_hours, dict):
        return []

    closed_days = []
    periods = opening_hours.get("periods", [])
    weekday_text = opening_hours.get("weekday_text", [])

    # 1. From weekday_text
    if weekday_text:
        for idx, text in enumerate(weekday_text):
            text_lower = text.lower()
            if "closed" in text_lower or "zárva" in text_lower:
                for d_idx, d_name in enumerate(DAY_NAMES_EN):
                    if text_lower.startswith(d_name.lower()):
                        closed_days.append({
                            "day_index_python": d_idx,
                            "day_en": d_name,
                            "day_hu": DAY_NAMES_HU[d_idx],
                            "reason": text
                        })
        if closed_days:
            return closed_days

    # 2. From structured periods (if a day has no period entries)
    if periods:
        open_days_google = set()
        for p in periods:
            open_info = p.get("open", {})
            if "day" in open_info:
                open_days_google.add(open_info["day"])

        for py_idx in range(7):
            google_day = (py_idx + 1) % 7
            if google_day not in open_days_google:
                closed_days.append({
                    "day_index_python": py_idx,
                    "day_en": DAY_NAMES_EN[py_idx],
                    "day_hu": DAY_NAMES_HU[py_idx],
                    "reason": f"No operating periods on {DAY_NAMES_EN[py_idx]}"
                })

    return closed_days


def validate_activity_time_slot(
    poi_or_hours: Union[Dict[str, Any], Any],
    date_str: str,
    start_time: str,
    duration_minutes: int = 90
) -> Dict[str, Any]:
    """
    Validates whether a scheduled activity fits within venue opening hours.
    Returns:
    - is_open: bool
    - warning: Optional warning message in Hungarian
    - conflict_type: None | 'closed_entire_day' | 'not_open_yet' | 'closes_during_visit'
    """
    opening_hours = poi_or_hours.get("opening_hours") if isinstance(poi_or_hours, dict) else getattr(poi_or_hours, "opening_hours", None)
    poi_name = poi_or_hours.get("name") if isinstance(poi_or_hours, dict) else getattr(poi_or_hours, "name", "Látványosság")

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        py_weekday = dt.weekday()
    except Exception:
        py_weekday = 0

    h_start, m_start = parse_time_string_hhmm(start_time)
    
    # Calculate end time
    start_minutes = h_start * 60 + m_start
    end_minutes = start_minutes + duration_minutes
    h_end, m_end = divmod(end_minutes, 60)
    h_end = h_end % 24

    # Check if closed entire day
    closed_days = get_closed_days_of_week(opening_hours)
    for cd in closed_days:
        if cd["day_index_python"] == py_weekday:
            return {
                "is_open": False,
                "conflict_type": "closed_entire_day",
                "warning": f"⚠️ Figyelem: '{poi_name}' {cd['day_hu']}i napokon zárva tart!",
                "day_hu": cd["day_hu"]
            }

    # Check start time
    is_open_start = is_poi_open_at_time(opening_hours, py_weekday, h_start, m_start)
    if not is_open_start:
        return {
            "is_open": False,
            "conflict_type": "not_open_yet",
            "warning": f"⚠️ '{poi_name}' még nem tart nyitva {start_time}-kor!",
            "day_hu": DAY_NAMES_HU[py_weekday]
        }

    # Check end time
    is_open_end = is_poi_open_at_time(opening_hours, py_weekday, h_end, m_end)
    if not is_open_end and duration_minutes >= 30:
        return {
            "is_open": True,
            "conflict_type": "closes_during_visit",
            "warning": f"⚠️ '{poi_name}' a látogatás ideje alatt ({h_end:02d}:{m_end:02d}) bezár!",
            "day_hu": DAY_NAMES_HU[py_weekday]
        }

    return {
        "is_open": True,
        "conflict_type": None,
        "warning": None,
        "day_hu": DAY_NAMES_HU[py_weekday]
    }


# ---------------------------------------------------------------------------
# 4. GEO-SPATIAL DISTANCE, TRANSIT & POI CLUSTERING METRICS
# ---------------------------------------------------------------------------

def calculate_haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Computes great-circle distance between two geographic coordinates in kilometers.
    """
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def estimate_transit_time_minutes(
    distance_km: float,
    mode: str = "auto"
) -> Tuple[int, str]:
    """
    Estimates realistic urban transit time (minutes) and chosen transport mode.
    - Walking (< 1.8 km): ~4.5 km/h -> ~13.3 min/km
    - Public Transit (1.8 - 15 km): ~22 km/h + 6 min transfer/wait
    - Highway / Airport Shuttle (> 15 km): ~45 km/h + 8 min buffer
    """
    if distance_km <= 0.05:
        return 2, "walk"

    if mode == "walk" or (mode == "auto" and distance_km <= 1.8):
        mins = max(3, int(round(distance_km * 13.3)))
        return mins, "walk"
    elif distance_km <= 15.0:
        mins = max(10, int(round((distance_km / 22.0) * 60.0 + 6.0)))
        return mins, "transit"
    else:
        mins = max(18, int(round((distance_km / 45.0) * 60.0 + 8.0)))
        return mins, "shuttle"


def estimate_airport_to_hotel_transit(
    hotel_lat: float,
    hotel_lon: float,
    city_lat: float,
    city_lon: float,
    airport_lat: Optional[float] = None,
    airport_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculates distance and transit time from airport to hotel.
    If exact airport coordinates are omitted, places an estimated international airport
    ~16-20 km outside the city center.
    """
    if airport_lat is not None and airport_lon is not None and (airport_lat != 0.0 or airport_lon != 0.0):
        a_lat, a_lon = airport_lat, airport_lon
    else:
        # Standard synthetic airport offset (~18km southwest / northeast)
        a_lat = city_lat + 0.12
        a_lon = city_lon + 0.15

    dist_km = calculate_haversine_distance_km(hotel_lat, hotel_lon, a_lat, a_lon)
    transit_mins, mode = estimate_transit_time_minutes(dist_km, mode="shuttle")

    # Airport accessibility subscore (0.0 to 10.0)
    # <= 20 min -> 10.0, 45 min -> 7.5, 75 min -> 5.0, > 100 min -> 2.0
    if transit_mins <= 20:
        airport_score = 10.0
    elif transit_mins <= 45:
        airport_score = 10.0 - ((transit_mins - 20) / 25.0) * 2.5
    elif transit_mins <= 80:
        airport_score = 7.5 - ((transit_mins - 45) / 35.0) * 3.5
    else:
        airport_score = max(1.0, 4.0 - ((transit_mins - 80) / 40.0) * 3.0)

    return {
        "airport_distance_km": dist_km,
        "transit_time_minutes": transit_mins,
        "transit_mode": mode,
        "airport_score_0_10": round(airport_score, 1)
    }


def analyze_hotel_poi_clustering(
    hotel_lat: float,
    hotel_lon: float,
    pois: List[Union[Dict[str, Any], Any]],
    walkable_radius_km: float = 1.5,
    nearby_radius_km: float = 3.5
) -> Dict[str, Any]:
    """
    Evaluates hotel proximity to city points of interest (attractions, dining, cultural hubs).
    Metrics calculated:
    - walkable_count: Number of POIs within 1.5 km (sétálható távolság)
    - nearby_count: Number of POIs within 3.5 km
    - avg_distance_top_pois_km: Average distance to the closest 8 POIs
    - poi_clustering_score: 0.0 to 10.0 score based on density and proximity
    """
    if not pois:
        return {
            "walkable_count": 0,
            "nearby_count": 0,
            "avg_distance_top_pois_km": 5.0,
            "poi_clustering_score_0_10": 5.0,
            "closest_pois": []
        }

    distances: List[Tuple[float, str, str]] = []

    for p in pois:
        p_name = p.get("name") if isinstance(p, dict) else getattr(p, "name", "Látványosság")
        p_cat = p.get("type") or p.get("category") if isinstance(p, dict) else getattr(p, "type", "attraction")

        loc = p.get("location") if isinstance(p, dict) else getattr(p, "location", None)
        if isinstance(loc, dict):
            p_lat = float(loc.get("lat") or 0.0)
            p_lon = float(loc.get("lng") or loc.get("lon") or 0.0)
        elif hasattr(loc, "lat") and hasattr(loc, "lng"):
            p_lat, p_lon = float(loc.lat), float(loc.lng)
        elif isinstance(p, dict) and "lat" in p and ("lon" in p or "lng" in p):
            p_lat = float(p.get("lat") or 0.0)
            p_lon = float(p.get("lon") or p.get("lng") or 0.0)
        else:
            p_lat, p_lon = hotel_lat, hotel_lon

        d = calculate_haversine_distance_km(hotel_lat, hotel_lon, p_lat, p_lon)
        distances.append((d, p_name, p_cat))

    distances.sort(key=lambda x: x[0])

    walkable = [d for d in distances if d[0] <= walkable_radius_km]
    nearby = [d for d in distances if d[0] <= nearby_radius_km]

    top_8 = distances[:8]
    avg_top_dist = sum(d[0] for d in top_8) / max(1, len(top_8))

    # Density & proximity score (0.0 - 10.0)
    # High count in walkable radius (> 6) -> 10.0
    walk_component = min(5.0, len(walkable) * 0.8)
    near_component = min(3.0, len(nearby) * 0.25)
    prox_component = max(0.0, min(2.0, (4.0 - avg_top_dist) * 0.6))

    cluster_score = max(1.0, min(10.0, walk_component + near_component + prox_component + 1.0))

    return {
        "walkable_count": len(walkable),
        "nearby_count": len(nearby),
        "avg_distance_top_pois_km": round(avg_top_dist, 2),
        "poi_clustering_score_0_10": round(cluster_score, 1),
        "closest_pois": [
            {"name": d[1], "category": d[2], "distance_km": round(d[0], 2)}
            for d in distances[:5]
        ]
    }


def calculate_normalized_location_score(
    hotel_lat: float,
    hotel_lon: float,
    city_lat: float,
    city_lon: float,
    pois: List[Union[Dict[str, Any], Any]],
    airport_lat: Optional[float] = None,
    airport_lon: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes a composite, normalized LocationScore (0.0 - 10.0) for an accommodation candidate.
    
    Formula:
    LocationScore = w_poi * S_poi_cluster + w_center * S_centrality + w_airport * S_airport
    Default weights: POI Cluster = 0.50, Center Distance = 0.30, Airport Transit = 0.20
    """
    w_poi = 0.50 if not weights else weights.get("poi", 0.50)
    w_center = 0.30 if not weights else weights.get("center", 0.30)
    w_airport = 0.20 if not weights else weights.get("airport", 0.20)

    # 1. POI Clustering analysis
    cluster_res = analyze_hotel_poi_clustering(hotel_lat, hotel_lon, pois)
    s_poi = cluster_res["poi_clustering_score_0_10"]

    # 2. City center proximity
    center_dist_km = calculate_haversine_distance_km(hotel_lat, hotel_lon, city_lat, city_lon)
    if center_dist_km <= 1.0:
        s_center = 10.0
    elif center_dist_km <= 3.0:
        s_center = 10.0 - (center_dist_km - 1.0) * 1.5
    elif center_dist_km <= 8.0:
        s_center = 7.0 - ((center_dist_km - 3.0) / 5.0) * 3.5
    else:
        s_center = max(1.0, 3.5 - ((center_dist_km - 8.0) / 10.0) * 2.5)

    # 3. Airport transit
    airport_res = estimate_airport_to_hotel_transit(
        hotel_lat, hotel_lon, city_lat, city_lon, airport_lat, airport_lon
    )
    s_airport = airport_res["airport_score_0_10"]

    # Composite Score (0.0 to 10.0)
    final_score_raw = (w_poi * s_poi) + (w_center * s_center) + (w_airport * s_airport)
    final_score = round(max(0.0, min(10.0, final_score_raw)), 1)

    # Classification tier
    if final_score >= 9.0:
        tier_label = "Kiváló elhelyezkedés (Központ & Látnivalók)"
        badge = "Kiváló elhelyezkedés"
    elif final_score >= 7.8:
        tier_label = "Nagyon jó elhelyezkedés (Sétálható)"
        badge = "Nagyon jó elhelyezkedés"
    elif final_score >= 6.0:
        tier_label = "Jó elhelyezkedés (Könnyű megközelítés)"
        badge = "Jó elhelyezkedés"
    else:
        tier_label = "Külvárosi / Csendes elhelyezkedés"
        badge = "Külvárosi"

    highlights = []
    if cluster_res["walkable_count"] >= 4:
        highlights.append(f"🚶 {cluster_res['walkable_count']} fő látnivaló sétatávra (<15 perc)")
    elif cluster_res["nearby_count"] >= 5:
        highlights.append(f"🚊 {cluster_res['nearby_count']} látványosság 10 perc alatt elérhető")

    if center_dist_km <= 1.5:
        highlights.append(f"🏛️ Belváros szívében ({center_dist_km:.1f} km a központtól)")
    elif center_dist_km <= 4.0:
        highlights.append(f"📍 Közeli belváros ({center_dist_km:.1f} km)")

    if airport_res["transit_time_minutes"] <= 35:
        highlights.append(f"✈️ Gyors reptéri transzfer (~{airport_res['transit_time_minutes']} perc)")

    return {
        "location_score": final_score,
        "tier_label": tier_label,
        "badge": badge,
        "subscores": {
            "poi_clustering": round(s_poi, 1),
            "centrality": round(s_center, 1),
            "airport_access": round(s_airport, 1)
        },
        "metrics": {
            "distance_to_center_km": round(center_dist_km, 2),
            "airport_distance_km": airport_res["airport_distance_km"],
            "airport_transit_mins": airport_res["transit_time_minutes"],
            "walkable_poi_count": cluster_res["walkable_count"],
            "nearby_poi_count": cluster_res["nearby_count"],
            "avg_top_poi_distance_km": cluster_res["avg_distance_top_pois_km"]
        },
        "highlights": highlights[:3],
        "closest_pois": cluster_res["closest_pois"]
    }
