"""
Optivoya — Unified Trip Scoring & Re-ranking Engine
Calculates the holistic TripScore (Level 1 + Level 2 AHP & Friction analysis)
for complete trip packages: Destination + Flight + Accommodation + Experiences + Logistics.
"""
import math
from typing import Dict, Any, List, Optional
from app.models.models import ExperiencePreferences, LogisticsPreferences


def calculate_experience_diversity(activities: List[Dict[str, Any]]) -> float:
    """
    Kiszámítja az élmények diverzitási pontszámát (0.0 - 1.0).
    A Shannon-entrópia normalizált változatát használja a kategória-eloszlásra.
    Magasabb diverzitás = kiegyensúlyozott élménycsomag (pl. gasztro + kultúra + kilátó).
    """
    if not activities:
        return 0.5

    cat_counts: Dict[str, int] = {}
    for a in activities:
        cat = a.get("category", "other")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    total = len(activities)
    if total <= 1:
        return 0.7

    # Shannon-entrópia
    entropy = 0.0
    for count in cat_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    # Elméleti maximum: log2(min(total_cats, 5))
    max_entropy = math.log2(min(max(len(cat_counts), 2), 5))
    if max_entropy <= 0:
        return 0.5

    diversity_ratio = min(1.0, entropy / max_entropy)
    return round(diversity_ratio, 3)


def calculate_unified_trip_score(
    destination: Optional[Dict[str, Any]] = None,
    flight: Optional[Dict[str, Any]] = None,
    accommodation: Optional[Dict[str, Any]] = None,
    activities: Optional[List[Dict[str, Any]]] = None,
    experience_preferences: Optional[Dict[str, float]] = None,
    logistics_preferences: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Kiszámítja az összefüggő utazás (Complete Trip) teljes pontszámát (0 - 100).
    
    Formula:
    Trip Score = (
        w_dest * DestScore + 
        w_flight * FlightScore + 
        w_stay * StayScore + 
        w_exp * ExperienceFitScore
    ) * DiversityMultiplier - FrictionPenalty
    """
    w_dest = 0.25
    w_flight = 0.25
    w_stay = 0.25
    w_exp = 0.25

    if weights:
        w_total = sum(weights.values()) or 1.0
        w_dest = weights.get("destination", weights.get("dest", 25.0)) / w_total
        w_flight = weights.get("flight", 25.0) / w_total
        w_stay = weights.get("accommodation", weights.get("stay", 25.0)) / w_total
        w_exp = weights.get("experience", 25.0) / w_total

    # 1. Destination Fit (0 - 100)
    dest_score = 75.0
    if destination:
        dest_score = float(destination.get("score", 75.0))

    # 2. Flight Fit & Effective Vacation Time (0 - 100)
    flight_score = 75.0
    effective_hours = 16.0
    if flight:
        # PROMETHEE relevancia vagy ár-menetidő arány
        flight_score = float(flight.get("relevance_pct", 78.0))
        effective_hours = float(flight.get("effective_vacation_hours", 16.0) or 16.0)
        # Bónusz / levonás a hasznos idő alapján
        if effective_hours >= 20.0:
            flight_score = min(99.0, flight_score + 4.0)
        elif effective_hours <= 10.0:
            flight_score = max(40.0, flight_score - 6.0)

    # 3. Accommodation Fit & Location (0 - 100)
    stay_score = 75.0
    if accommodation:
        rating_10 = float(accommodation.get("rating", 8.0))
        stay_score = min(99.0, rating_10 * 10.0)
        # Csillag és lokáció bónusz
        if accommodation.get("is_market_benchmark") or "belváros" in str(accommodation.get("address", "")).lower() or "óváros" in str(accommodation.get("address", "")).lower():
            stay_score = min(99.0, stay_score + 3.0)

    # 4. Experience Fit & Diversity (0 - 100)
    activities = activities or []
    diversity = calculate_experience_diversity(activities)
    
    # Kategóriailleszkedés
    exp_fit_score = 80.0
    if activities and experience_preferences:
        # Kategóriák aránya a kiválasztott élményekben
        cat_matches = 0
        top_prefs = [k for k, v in experience_preferences.items() if v >= 60]
        for a in activities:
            cat = a.get("category", "")
            if any(p in cat for p in top_prefs):
                cat_matches += 1
        match_ratio = cat_matches / max(len(activities), 1)
        exp_fit_score = 60.0 + (match_ratio * 30.0) + (diversity * 10.0)
        exp_fit_score = min(99.0, exp_fit_score)
    elif activities:
        exp_fit_score = 70.0 + (diversity * 25.0)

    # 5. Súrlódási levonás (Friction Penalty)
    friction_penalty = 0.0
    if flight:
        stops = int(flight.get("out_stops", 0)) + int(flight.get("in_stops", 0))
        if stops >= 2:
            friction_penalty += 4.0
        elif stops == 1:
            friction_penalty += 1.5

    # Alap kalkuláció
    raw_trip_score = (
        (w_dest * dest_score) +
        (w_flight * flight_score) +
        (w_stay * stay_score) +
        (w_exp * exp_fit_score)
    ) - friction_penalty

    trip_score = round(max(45.0, min(99.0, raw_trip_score)), 1)

    # Pozitív fénypontok & indoklások
    strengths = []
    if dest_score >= 80.0:
        strengths.append(f"Kiváló célállomás-illeszkedés ({int(dest_score)}/100 pont)")
    if flight and effective_hours >= 18.0:
        strengths.append(f"Kiemelkedő hasznos utazási idő (~{int(effective_hours)} óra szabadidő az 1. és utolsó napon)")
    elif flight and flight_score >= 80.0:
        strengths.append(f"Kedvező menetrend és repülőjegy opció")
    if stay_score >= 85.0:
        strengths.append(f"Kiváló minősítésű szállás ideális környéken ({int(stay_score)}/100 pont)")
    if diversity >= 0.70:
        strengths.append(f"Kiegyensúlyozott, változatos élménykínálat (Kultúra, gasztro és pihenés)")

    tradeoffs = []
    if friction_penalty >= 3.0:
        tradeoffs.append("Többszöri átszállás a repülőúton")
    if flight and effective_hours <= 12.0:
        tradeoffs.append("Késői érkezés vagy kora reggeli visszaindulás miatt szűkebb hasznos idő")

    return {
        "trip_score": trip_score,
        "subscores": {
            "destination": round(dest_score, 1),
            "flight": round(flight_score, 1),
            "accommodation": round(stay_score, 1),
            "experience": round(exp_fit_score, 1),
            "diversity": round(diversity * 100.0, 1),
            "friction_penalty": round(friction_penalty, 1)
        },
        "effective_vacation_hours": effective_hours,
        "strengths": strengths[:3],
        "tradeoffs": tradeoffs,
        "recommendation_summary": " • ".join(strengths[:2]) if strengths else "Harmonikus utazási csomag"
    }
