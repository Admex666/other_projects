"""
Optivoya — Dummy / Simulation Planner Service
Gyors, szimulált adatokat generál a Master Planner teszteléséhez (0 Browserless és API token költség).
Kizárólag jogosult tesztelőknek (username='bean' vagy admin / id IN (1, 2)).
"""
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.destination_service import get_filtered_destinations
from app.services.accommodation_market_service import generate_market_benchmark_stays

# Célállomások offline referenciaprofilja (élethű repülőjegy árak, Numbeo költség, klíma és biztonság)
DUMMY_DEST_PROFILES = {
    "Róma": {
        "country": "Olaszország",
        "region": "Europe",
        "airport": "FCO",
        "base_flight_huf": 28900,
        "daily_cost_huf": 17500,
        "hotel_nightly_huf": 28000,
        "temp": 24.5,
        "safety": 72,
        "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80",
        "highlights": "Kiváló őszi időjárás, pezsgő gasztronómia és kedvező közvetlen járatok."
    },
    "Barcelona": {
        "country": "Spanyolország",
        "region": "Europe",
        "airport": "BCN",
        "base_flight_huf": 32500,
        "daily_cost_huf": 18500,
        "hotel_nightly_huf": 31000,
        "temp": 25.0,
        "safety": 70,
        "image": "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=800&q=80",
        "highlights": "Közvetlen tengerpart, gazdag építészet és meleg mediterrán éghajlat."
    },
    "Nizza": {
        "country": "Franciaország",
        "region": "Europe",
        "airport": "NCE",
        "base_flight_huf": 34800,
        "daily_cost_huf": 22000,
        "hotel_nightly_huf": 36000,
        "temp": 23.8,
        "safety": 78,
        "image": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=800&q=80",
        "highlights": "Francia Riviéra, elegáns tengerparti sétány és kellemes napsütés."
    },
    "Lisszabon": {
        "country": "Portugália",
        "region": "Europe",
        "airport": "LIS",
        "base_flight_huf": 38900,
        "daily_cost_huf": 16200,
        "hotel_nightly_huf": 26500,
        "temp": 24.2,
        "safety": 84,
        "image": "https://images.unsplash.com/photo-1509840841025-9088ba78a826?auto=format&fit=crop&w=800&q=80",
        "highlights": "Biztonságos város, kiváló óceáni klíma és pénztárcabarát árszínvonal."
    },
    "Athén": {
        "country": "Görögország",
        "region": "Europe",
        "airport": "ATH",
        "base_flight_huf": 36500,
        "daily_cost_huf": 15800,
        "hotel_nightly_huf": 24000,
        "temp": 26.5,
        "safety": 74,
        "image": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=800&q=80",
        "highlights": "Hosszú napsütéses órák, ókori műemlékek és autentikus tavernák."
    },
    "Valencia": {
        "country": "Spanyolország",
        "region": "Europe",
        "airport": "VLC",
        "base_flight_huf": 35200,
        "daily_cost_huf": 16900,
        "hotel_nightly_huf": 27500,
        "temp": 25.4,
        "safety": 82,
        "image": "https://images.unsplash.com/photo-1599553597652-9ea37e199f8d?auto=format&fit=crop&w=800&q=80",
        "highlights": "Kiváló kerékpáros infrastruktúra, tengerpart és gazdag kulturális élet."
    },
    "Palma de Mallorca": {
        "country": "Spanyolország",
        "region": "Europe",
        "airport": "PMI",
        "base_flight_huf": 37900,
        "daily_cost_huf": 19500,
        "hotel_nightly_huf": 32000,
        "temp": 26.0,
        "safety": 80,
        "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=800&q=80",
        "highlights": "Kristálytiszta öblök, festői óváros és ideális fürdőzési feltételek."
    },
    "Dubrovnik": {
        "country": "Horvátország",
        "region": "Europe",
        "airport": "DBV",
        "base_flight_huf": 39500,
        "daily_cost_huf": 21000,
        "hotel_nightly_huf": 34000,
        "temp": 24.8,
        "safety": 85,
        "image": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=800&q=80",
        "highlights": "Középkori várfalak, adriai panoráma és magas biztonsági mutatók."
    },
    "Bécs": {
        "country": "Ausztria",
        "region": "Europe",
        "airport": "VIE",
        "base_flight_huf": 22000,
        "daily_cost_huf": 24000,
        "hotel_nightly_huf": 33000,
        "temp": 20.5,
        "safety": 88,
        "image": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=800&q=80",
        "highlights": "Közeli elérhetőség, világszínvonalú múzeumok és prémium kávéházi kultúra."
    },
    "Málta": {
        "country": "Málta",
        "region": "Europe",
        "airport": "MLA",
        "base_flight_huf": 33500,
        "daily_cost_huf": 17800,
        "hotel_nightly_huf": 27000,
        "temp": 26.2,
        "safety": 81,
        "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=800&q=80",
        "highlights": "Napfényes szigetvilág, gazdag történelem és kedvező járatlehetőségek."
    }
}

def generate_dummy_destinations(intake_data: Any) -> List[Dict[str, Any]]:
    """
    Strukturált, szimulált célállomás-eredményeket állít elő azonnal (0 token felhasználással).
    A rangsorolás és a pontozás a megadott prioritási súlyok (AHP) és célhőmérséklet szerint kalkulálódik.
    """
    target_temp = float(getattr(intake_data, "target_temp", 24.0) or 24.0)
    adults = max(1, int(getattr(intake_data, "adults", 2) or 2))
    duration = max(1, int(getattr(intake_data, "duration", 7) or 7))
    
    weights = getattr(intake_data, "ahp_weights", None) or {
        "total_cost": getattr(intake_data, "weight_total_cost", 34.0),
        "weather": getattr(intake_data, "weight_weather", 33.0),
        "safety": getattr(intake_data, "weight_safety", 33.0)
    }

    w_cost = float(weights.get("total_cost", 34.0)) / 100.0
    w_weather = float(weights.get("weather", 33.0)) / 100.0
    w_safety = float(weights.get("safety", 33.0)) / 100.0

    exclusions = getattr(intake_data, "exclusions", []) or []
    preferred_regions = getattr(intake_data, "preferred_regions", []) or []

    candidates = []
    for name, prof in DUMMY_DEST_PROFILES.items():
        if name.lower() in [e.lower() for e in exclusions]:
            continue
        if preferred_regions and "all" not in preferred_regions and prof["region"] not in preferred_regions:
            continue

        flight_price = prof["base_flight_huf"] * adults
        daily_cost = prof["daily_cost_huf"]
        stay_cost = prof["hotel_nightly_huf"] * duration
        total_trip_cost = flight_price + (daily_cost * duration * adults) + stay_cost

        # Részpontszámok (0 - 100)
        temp_diff = abs(prof["temp"] - target_temp)
        weather_score = max(40.0, 100.0 - (temp_diff * 7.5))
        
        # Költség pontszám: olcsóbb jobb (150e Ft és 450e Ft között skálázva)
        cost_score = max(35.0, min(98.0, 100.0 - ((total_trip_cost - 150000) / 4000.0)))
        
        safety_score = float(prof["safety"])

        # Összesített súlyozott pontszám
        composite_score = round((w_cost * cost_score) + (w_weather * weather_score) + (w_safety * safety_score), 1)
        composite_score = max(55.0, min(99.0, composite_score))

        candidates.append({
            "name": name,
            "city": name,
            "country": prof["country"],
            "region": prof["region"],
            "score": composite_score,
            "explanation": f"{prof['highlights']} (Szimulált tesztadat)",
            "image": prof["image"],
            "is_dummy": True,
            "metrics": {
                "temp_raw": prof["temp"],
                "temp_celsius": prof["temp"],
                "temp_formatted": f"{prof['temp']:.1f}°C",
                "flight_price_raw": flight_price,
                "flight_price_huf": flight_price,
                "flight_price_formatted": f"{flight_price:,.0f} Ft".replace(",", " "),
                "safety_raw": safety_score,
                "safety": safety_score,
                "safety_score": safety_score,
                "daily_cost_raw": round(daily_cost / 400.0, 1),
                "daily_cost_raw_huf": daily_cost,
                "daily_cost_formatted": f"{daily_cost:,.0f} Ft/nap".replace(",", " "),
                "daily_cost_huf_formatted": f"{daily_cost:,.0f} Ft/nap".replace(",", " "),
                "hotel_nightly_raw": prof["hotel_nightly_huf"],
                "hotel_nightly_formatted": f"{prof['hotel_nightly_huf']:,.0f} Ft/éj".replace(",", " "),
                "total_trip_cost_huf": total_trip_cost
            }
        })

    # Rendezés pontszám szerint
    candidates.sort(key=lambda x: x["score"], reverse=True)
    for idx, c in enumerate(candidates):
        c["rank"] = idx + 1

    return candidates

def generate_dummy_flights(req: Any) -> List[Dict[str, Any]]:
    """
    Élethű, szimulált járatkombinációkat állít elő azonnal (0 Kiwi és 0 Browserless hívás).
    """
    origin = getattr(req, "origin", "Budapest")
    dest = getattr(req, "destination", "Róma")
    adults = max(1, int(getattr(req, "adults", 2) or 2))
    duration_days = max(1, int(getattr(req, "duration", 7) or 7))
    direct_only = bool(getattr(req, "direct_only", False))

    dest_clean = dest.split("(")[0].strip()
    profile = DUMMY_DEST_PROFILES.get(dest_clean, {
        "airport": dest_clean[:3].upper(),
        "base_flight_huf": 32000
    })

    dest_airport = profile.get("airport", "FCO")
    origin_airport = "BUD"

    # Dátumok megállapítása
    if getattr(req, "exact_out_date", None) and getattr(req, "exact_in_date", None):
        out_date_str = req.exact_out_date
        in_date_str = req.exact_in_date
    elif getattr(req, "out_from", None):
        out_date_str = req.out_from
        try:
            d_out = datetime.strptime(req.out_from, "%Y-%m-%d")
            in_date_str = (d_out + timedelta(days=duration_days)).strftime("%Y-%m-%d")
        except Exception:
            in_date_str = "2026-09-17"
    else:
        year = getattr(req, "year", 2026) or 2026
        month = getattr(req, "month", 9) or 9
        out_date_str = f"{year}-{int(month):02d}-12"
        in_date_str = f"{year}-{int(month):02d}-19"

    base_price = profile.get("base_flight_huf", 32000)

    # 6 db változatos repülési opció
    flight_templates = [
        {
            "carrier": "Wizz Air",
            "stops": 0,
            "out_dep": "06:15", "out_arr": "08:20", "out_dur": 2.1,
            "in_dep": "21:30", "in_arr": "23:35", "in_dur": 2.1,
            "price_mult": 0.95,
            "phi_net": 0.88,
            "relevance": 96
        },
        {
            "carrier": "Ryanair",
            "stops": 0,
            "out_dep": "13:30", "out_arr": "15:35", "out_dur": 2.1,
            "in_dep": "16:15", "in_arr": "18:20", "in_dur": 2.1,
            "price_mult": 1.02,
            "phi_net": 0.82,
            "relevance": 93
        },
        {
            "carrier": "Wizz Air",
            "stops": 0,
            "out_dep": "18:40", "out_arr": "20:45", "out_dur": 2.1,
            "in_dep": "09:10", "in_arr": "11:15", "in_dur": 2.1,
            "price_mult": 1.08,
            "phi_net": 0.76,
            "relevance": 88
        },
        {
            "carrier": "Lufthansa",
            "stops": 1,
            "out_dep": "09:20", "out_arr": "13:45", "out_dur": 4.4,
            "in_dep": "14:15", "in_arr": "18:30", "in_dur": 4.25,
            "price_mult": 1.65,
            "phi_net": 0.58,
            "relevance": 78
        },
        {
            "carrier": "Austrian Airlines",
            "stops": 1,
            "out_dep": "07:10", "out_arr": "11:55", "out_dur": 4.75,
            "in_dep": "17:40", "in_arr": "22:15", "in_dur": 4.6,
            "price_mult": 1.78,
            "phi_net": 0.52,
            "relevance": 73
        },
        {
            "carrier": "Ryanair",
            "stops": 0,
            "out_dep": "10:15", "out_arr": "12:20", "out_dur": 2.1,
            "in_dep": "19:45", "in_arr": "21:50", "in_dur": 2.1,
            "price_mult": 1.15,
            "phi_net": 0.72,
            "relevance": 86
        }
    ]

    flights = []
    for idx, tpl in enumerate(flight_templates):
        if direct_only and tpl["stops"] > 0:
            continue

        unit_price = round(base_price * tpl["price_mult"], -2)
        total_price = unit_price * adults

        flights.append({
            "rank": len(flights) + 1,
            "out_dep_time": f"{out_date_str}T{tpl['out_dep']}:00",
            "out_arr_time": f"{out_date_str}T{tpl['out_arr']}:00",
            "in_dep_time": f"{in_date_str}T{tpl['in_dep']}:00",
            "in_arr_time": f"{in_date_str}T{tpl['in_arr']}:00",
            "out_carriers": tpl["carrier"],
            "in_carriers": tpl["carrier"],
            "out_stops": tpl["stops"],
            "in_stops": tpl["stops"],
            "out_duration_h": tpl["out_dur"],
            "in_duration_h": tpl["in_dur"],
            "out_dep_airport": origin_airport,
            "out_arr_airport": dest_airport,
            "in_dep_airport": dest_airport,
            "in_arr_airport": origin_airport,
            "price_huf": total_price,
            "total_price_huf": total_price,
            "stay_days": duration_days,
            "stay_diff_days": 0.0,
            "phi_net": tpl["phi_net"],
            "relevance_pct": tpl["relevance"],
            "is_dummy": True
        })

    return flights

def generate_dummy_stays(req: Any) -> List[Dict[str, Any]]:
    """
    Élethű, strukturált szállásopciókat készít azonnal (0 Cozycozy és 0 Browserless hívás).
    """
    city_clean = getattr(req, "city", "Róma").strip()
    country_clean = getattr(req, "country", "").strip()
    checkin = getattr(req, "checkin", "2026-09-12")
    checkout = getattr(req, "checkout", "2026-09-19")
    adults = max(1, int(getattr(req, "adults", 2) or 2))
    hotel_types = getattr(req, "hotel_types", None)
    breakfast = bool(getattr(req, "breakfast", False))
    amenities = getattr(req, "amenities", None)

    stays = generate_market_benchmark_stays(
        city=city_clean,
        country=country_clean,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        hotel_types=hotel_types,
        breakfast=breakfast,
        amenities=amenities
    )

    for st in stays:
        st["is_dummy"] = True
        st["source"] = "dummy_simulation_mode"

    return stays
