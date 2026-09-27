"""
Unit and Integration Tests for Optivoya Geo & Experience Intelligence Layer.
Tests:
1. 12-dimensional vector normalization & alias mapping
2. Mathematical cosine similarity & experience fit calculation
3. Activity fit scoring
4. Opening hours parsing, closure detection, and schedule validation
5. Haversine distance & transit time estimation
6. Hotel-to-POI clustering & LocationScore (0.0 to 10.0) computation
"""

import math
import pytest
from app.services.geo_experience_layer import (
    DIMENSIONS_12,
    normalize_preference_vector,
    extract_destination_vector,
    calculate_cosine_similarity,
    calculate_experience_fit_12d,
    calculate_activity_fit_score,
    is_poi_open_at_time,
    get_closed_days_of_week,
    validate_activity_time_slot,
    calculate_haversine_distance_km,
    estimate_transit_time_minutes,
    estimate_airport_to_hotel_transit,
    analyze_hotel_poi_clustering,
    calculate_normalized_location_score,
)
from app.services.experience_intelligence_service import ExperienceIntelligenceService
from app.services import maps_service
from app.models.models import ExperiencePreferences, POI, POILocation


def test_12d_vector_normalization():
    """Tests normalization of user preferences from dictionary, model, and tag list."""
    # 1. From dict with synonyms
    raw_dict = {"culture": 80.0, "gastronomy": 90.0, "beach": 50.0, "nightlife": 30.0}
    norm_vec = normalize_preference_vector(raw_dict)
    assert len(norm_vec) == 12
    assert pytest.approx(sum(norm_vec.values()), 0.001) == 1.0
    assert norm_vec["culture"] > norm_vec["nightlife"]
    assert norm_vec["food"] > norm_vec["beach"]  # gastronomy mapped to food

    # 2. From ExperiencePreferences pydantic model
    exp_model = ExperiencePreferences(culture=90.0, gastronomy=95.0, nature=70.0, nightlife=10.0)
    norm_vec_model = normalize_preference_vector(exp_model)
    assert pytest.approx(sum(norm_vec_model.values()), 0.001) == 1.0
    assert norm_vec_model["food"] > norm_vec_model["nightlife"]

    # 3. From interest tags
    tags = ["culture", "gastronomy", "beach"]
    norm_vec_tags = normalize_preference_vector(tags)
    assert norm_vec_tags["culture"] == norm_vec_tags["food"] == norm_vec_tags["beach"]
    assert norm_vec_tags["adventure"] == 0.0


def test_cosine_similarity_edge_cases():
    """Tests mathematical correctness of cosine similarity."""
    # Identical vectors
    v1 = {"culture": 1.0, "food": 0.5, "beach": 0.0}
    assert pytest.approx(calculate_cosine_similarity(v1, v1), 0.001) == 1.0

    # Orthogonal vectors
    v2 = {"culture": 1.0, "food": 0.0, "beach": 0.0}
    v3 = {"culture": 0.0, "food": 1.0, "beach": 0.0}
    assert pytest.approx(calculate_cosine_similarity(v2, v3), 0.001) == 0.0

    # Scaled vectors (cosine similarity is scale-invariant)
    v4 = {"culture": 2.0, "food": 4.0}
    v5 = {"culture": 10.0, "food": 20.0}
    assert pytest.approx(calculate_cosine_similarity(v4, v5), 0.001) == 1.0


def test_experience_fit_12d():
    """Tests matching client preferences against destination profile."""
    user_prefs = {"culture": 95.0, "food": 90.0, "beach": 10.0, "nightlife": 20.0}
    
    # Destination A: Cultural food hub (Rome/Paris style)
    dest_culture = {
        "experience_vector": {
            "dimensions": {
                "culture": {"absolute": 98.0},
                "food": {"absolute": 95.0},
                "beach": {"absolute": 20.0},
                "nature": {"absolute": 60.0},
                "nightlife": {"absolute": 75.0},
                "romance": {"absolute": 85.0},
                "authenticity": {"absolute": 90.0},
                "locality": {"absolute": 85.0},
                "walkability": {"absolute": 90.0},
                "tourist_intensity": {"absolute": 70.0},
                "adventure": {"absolute": 30.0},
                "family": {"absolute": 60.0}
            }
        }
    }
    
    # Destination B: Beach party island (Ibiza style)
    dest_party_beach = {
        "experience_vector": {
            "dimensions": {
                "culture": {"absolute": 30.0},
                "food": {"absolute": 50.0},
                "beach": {"absolute": 98.0},
                "nature": {"absolute": 70.0},
                "nightlife": {"absolute": 99.0},
                "romance": {"absolute": 60.0},
                "authenticity": {"absolute": 40.0},
                "locality": {"absolute": 45.0},
                "walkability": {"absolute": 50.0},
                "tourist_intensity": {"absolute": 90.0},
                "adventure": {"absolute": 65.0},
                "family": {"absolute": 40.0}
            }
        }
    }

    fit_culture = calculate_experience_fit_12d(user_prefs, dest_culture)
    fit_party = calculate_experience_fit_12d(user_prefs, dest_party_beach)

    assert fit_culture["fit_score_percent"] > fit_party["fit_score_percent"]
    assert fit_culture["cosine_similarity"] > fit_party["cosine_similarity"]
    assert len(fit_culture["top_matching_dimensions"]) > 0
    assert fit_culture["top_matching_dimensions"][0]["dimension"] in ["culture", "food"]


def test_activity_fit_scoring():
    """Tests activity-level preference matching."""
    user_prefs = {"culture": 90.0, "food": 95.0, "adventure": 10.0}
    
    museum = {"category": "attraction", "type": "museum", "rating": 4.8, "name": "Városi Múzeum"}
    food_tour = {"category": "food_market", "type": "restaurant", "rating": 4.9, "name": "Helyi Gasztrotúra"}
    skydiving = {"category": "active_adventure", "type": "adventure", "rating": 4.5, "name": "Ejtőernyőzés"}

    score_museum = calculate_activity_fit_score(museum, user_prefs)
    score_food = calculate_activity_fit_score(food_tour, user_prefs)
    score_sky = calculate_activity_fit_score(skydiving, user_prefs)

    assert score_museum > score_sky
    assert score_food > score_sky


def test_opening_hours_and_closure_detection():
    """Tests detection of closed days (e.g. Monday museum closures)."""
    # Museum schedule: Closed on Mondays (Python weekday 0), open Tue-Sun 09:00 - 18:00
    museum_hours = {
        "periods": [
            {"open": {"day": d, "time": "0900"}, "close": {"day": d, "time": "1800"}}
            for d in [0, 2, 3, 4, 5, 6]  # 0=Sunday, 2=Tuesday.. 6=Saturday (Monday=1 omitted)
        ],
        "weekday_text": [
            "Monday: Closed",
            "Tuesday: 9:00 AM – 6:00 PM",
            "Wednesday: 9:00 AM – 6:00 PM",
            "Thursday: 9:00 AM – 6:00 PM",
            "Friday: 9:00 AM – 6:00 PM",
            "Saturday: 9:00 AM – 6:00 PM",
            "Sunday: 9:00 AM – 6:00 PM"
        ]
    }

    closed_days = get_closed_days_of_week(museum_hours)
    assert len(closed_days) == 1
    assert closed_days[0]["day_hu"] == "Hétfő"

    # Test open on Tuesday 11:00
    assert is_poi_open_at_time(museum_hours, weekday_python=1, hour=11, minute=0) is True
    # Test closed on Monday 11:00
    assert is_poi_open_at_time(museum_hours, weekday_python=0, hour=11, minute=0) is False
    # Test closed on Tuesday 21:00 (past closing time)
    assert is_poi_open_at_time(museum_hours, weekday_python=1, hour=21, minute=0) is False

    # Validation slot on a Monday
    monday_date = "2026-09-28"  # 2026-09-28 is a Monday
    val_res = validate_activity_time_slot({"name": "Nemzeti Galéria", "opening_hours": museum_hours}, monday_date, "10:00", 120)
    assert val_res["is_open"] is False
    assert val_res["conflict_type"] == "closed_entire_day"
    assert "Hétfő" in val_res["warning"]


def test_haversine_and_transit_time():
    """Tests geographic distance and urban transit calculations."""
    # Barcelona Placa de Catalunya to Sagrada Familia (~2.2 km)
    cat_lat, cat_lon = 41.3870, 2.1700
    sag_lat, sag_lon = 41.4036, 2.1744

    dist_km = calculate_haversine_distance_km(cat_lat, cat_lon, sag_lat, sag_lon)
    assert 1.5 < dist_km < 3.0

    transit_mins, mode = estimate_transit_time_minutes(dist_km)
    assert 5 <= transit_mins <= 25


def test_normalized_location_score():
    """Tests composite LocationScore (0.0 to 10.0) computation."""
    city_lat, city_lon = 41.3851, 2.1734  # Barcelona center
    hotel_lat, hotel_lon = 41.3870, 2.1700  # Central hotel (~0.3 km from center)

    # Mock central POIs
    pois = [
        {"name": "Gothic Quarter", "type": "attraction", "location": {"lat": 41.3830, "lng": 2.1760}},
        {"name": "Picasso Museum", "type": "attraction", "location": {"lat": 41.3850, "lng": 2.1810}},
        {"name": "Mercat de la Boqueria", "type": "restaurant", "location": {"lat": 41.3817, "lng": 2.1716}},
        {"name": "Casa Batllo", "type": "attraction", "location": {"lat": 41.3917, "lng": 2.1649}},
        {"name": "Casa Mila", "type": "attraction", "location": {"lat": 41.3954, "lng": 2.1619}},
        {"name": "Palau de la Musica", "type": "attraction", "location": {"lat": 41.3876, "lng": 2.1753}},
    ]

    res = calculate_normalized_location_score(
        hotel_lat=hotel_lat,
        hotel_lon=hotel_lon,
        city_lat=city_lat,
        city_lon=city_lon,
        pois=pois
    )

    score = res["location_score"]
    assert 0.0 <= score <= 10.0
    assert score >= 8.0  # Central hotel with 6 walkable POIs should get >= 8.0
    assert res["metrics"]["walkable_poi_count"] >= 4
    assert len(res["highlights"]) > 0


def test_experience_intelligence_service_facade():
    """Tests high-level ExperienceIntelligenceService integration."""
    fit = ExperienceIntelligenceService.calculate_experience_fit(
        user_preferences={"culture": 90.0, "food": 95.0},
        destination_id_or_profile="barcelona"
    )
    assert "fit_score_percent" in fit
    assert "cosine_similarity" in fit
    assert fit["cosine_similarity"] > 0.70

    curated = ExperienceIntelligenceService.get_curated_activities(
        city_name="Barcelona",
        duration_days=3,
        user_preferences={"culture": 100.0, "food": 90.0}
    )
    assert len(curated) >= 4
    assert all("name" in c and "rating" in c for c in curated)
