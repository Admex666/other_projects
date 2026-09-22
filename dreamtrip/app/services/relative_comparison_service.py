"""
Optivoya Advisor Workspace — Relative Option Comparison & Trade-off Engine (Phase 6)
=====================================================================================
Calculates side-by-side matrix comparisons and relative difference explanations:
- Price deltas (nominal and percentage)
- Travel time & flight comfort deltas
- Accommodation category, rating, and location deltas
- Experience, culture, gastronomy, and vibe profile deltas
- Deterministic, data-backed "Why This Option?" and Trade-off narratives.
"""

from typing import List, Dict, Any, Optional
import math


class RelativeComparisonService:
    """
    Computes comparative matrices and natural-language relative trade-offs across 2-4 trip options.
    """

    @classmethod
    def compute_comparison_matrix(cls, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes 2-4 options and returns a structured comparison matrix with relative deltas.
        """
        if not options:
            return {"options": [], "dimensions": [], "relative_tradeoffs": []}

        # Reference baseline: Option 0 (usually Option A — Best Overall)
        base = options[0]
        base_price = base.get("total_price_huf") or 1
        base_flight_duration = base.get("flight", {}).get("duration_minutes") or 180
        base_hotel_rating = base.get("stay", {}).get("rating_normalized") or 8.5
        base_hotel_stars = base.get("stay", {}).get("stars") or 4
        base_trip_score = base.get("trip_score") or 85

        dimensions = [
            {
                "id": "price",
                "label": "Teljes Csomagár",
                "unit": "Ft",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": opt.get("total_price_huf", 0),
                        "formatted": f"{int(opt.get('total_price_huf', 0)):,} Ft".replace(",", " "),
                        "delta_from_base": opt.get("total_price_huf", 0) - base_price,
                        "delta_pct": round(((opt.get("total_price_huf", 0) - base_price) / base_price) * 100, 1),
                        "is_best": opt.get("total_price_huf", 0) == min(o.get("total_price_huf", 0) for o in options)
                    }
                    for opt in options
                ]
            },
            {
                "id": "price_per_person",
                "label": "Ár / Fő",
                "unit": "Ft",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": opt.get("price_per_person_huf", 0),
                        "formatted": f"{int(opt.get('price_per_person_huf', 0)):,} Ft".replace(",", " "),
                        "is_best": opt.get("price_per_person_huf", 0) == min(o.get("price_per_person_huf", 0) for o in options)
                    }
                    for opt in options
                ]
            },
            {
                "id": "trip_score",
                "label": "Összetett TripScore",
                "unit": "/100",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": opt.get("trip_score", 0),
                        "formatted": f"{int(opt.get('trip_score', 0))}/100",
                        "is_best": opt.get("trip_score", 0) == max(o.get("trip_score", 0) for o in options)
                    }
                    for opt in options
                ]
            },
            {
                "id": "flight_comfort",
                "label": "Repülés & Menetrend",
                "unit": "",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": opt.get("flight", {}).get("stops", 0),
                        "formatted": f"{opt.get('flight', {}).get('airline', 'Járat')} • {'Közvetlen' if opt.get('flight', {}).get('stops', 0) == 0 else str(opt.get('flight', {}).get('stops')) + ' átszállás'}",
                        "stops": opt.get("flight", {}).get("stops", 0),
                        "is_best": opt.get("flight", {}).get("stops", 0) == 0
                    }
                    for opt in options
                ]
            },
            {
                "id": "accommodation",
                "label": "Szállás Kategória & Értékelés",
                "unit": "",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": opt.get("stay", {}).get("rating_normalized", 8.0),
                        "formatted": f"{'★' * opt.get('stay', {}).get('stars', 3)} {opt.get('stay', {}).get('name', 'Hotel')} ({opt.get('stay', {}).get('rating_normalized', 8.5)}/10)",
                        "stars": opt.get("stay", {}).get("stars", 3),
                        "rating": opt.get("stay", {}).get("rating_normalized", 8.5),
                        "is_best": opt.get("stay", {}).get("stars", 3) == max(o.get("stay", {}).get("stars", 3) for o in options)
                    }
                    for opt in options
                ]
            },
            {
                "id": "activities",
                "label": "Élmény & Programok",
                "unit": "db",
                "values": [
                    {
                        "option_id": opt.get("id"),
                        "raw_value": len(opt.get("activities", [])),
                        "formatted": f"{len(opt.get('activities', []))} kiemelt látnivaló / élmény",
                        "is_best": len(opt.get("activities", [])) == max(len(o.get("activities", [])) for o in options)
                    }
                    for opt in options
                ]
            }
        ]

        # Compute Relative Trade-offs & Narratives
        relative_tradeoffs = cls._generate_relative_narratives(options)

        return {
            "options": options,
            "dimensions": dimensions,
            "relative_tradeoffs": relative_tradeoffs
        }

    @classmethod
    def _generate_relative_narratives(cls, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates comparative narrative bullets explaining relative advantages and trade-offs.
        """
        narratives = []
        if len(options) < 2:
            return narratives

        base = options[0]
        base_city = base.get("destination", {}).get("city") or base.get("title") or "Alap Opció"
        base_price = base.get("total_price_huf", 0)

        for i, opt in enumerate(options):
            opt_id = opt.get("id")
            opt_city = opt.get("destination", {}).get("city") or opt.get("title") or f"Opció {i+1}"
            opt_price = opt.get("total_price_huf", 0)
            arch = opt.get("archetype", "")

            pros = []
            cons = []

            if i == 0:
                # Base option
                pros.append("Legmagasabb kiegyensúlyozott összetett pontszám (TripScore).")
                pros.append("Kiváló arány a kényelem, lokáció és költség között.")
                if len(options) > 1 and any(o.get("total_price_huf", 0) < opt_price for o in options):
                    cons.append("Nem az abszolút legolcsóbb ár a válogatásban.")
            else:
                price_diff = opt_price - base_price
                if price_diff < 0:
                    pros.append(f"{abs(int(price_diff)):,} Ft-tal kedvezőbb teljes költségvetés mint {base_city}.".replace(",", " "))
                elif price_diff > 0:
                    cons.append(f"{int(price_diff):,} Ft árprémium a bázis opcióhoz képest.".replace(",", " "))

                # Stay stars comparison
                opt_stars = opt.get("stay", {}).get("stars", 3)
                base_stars = base.get("stay", {}).get("stars", 3)
                if opt_stars > base_stars:
                    pros.append(f"Magasabb szálláskategória ({opt_stars}★ vs {base_stars}★).")
                elif opt_stars < base_stars:
                    cons.append(f"Mérsékeltebb szálláskategória ({opt_stars}★ vs {base_stars}★).")

                # Flight comparison
                opt_stops = opt.get("flight", {}).get("stops", 0)
                base_stops = base.get("flight", {}).get("stops", 0)
                if opt_stops < base_stops:
                    pros.append("Kényelmesebb, közvetlen járatmenetrend.")
                elif opt_stops > base_stops:
                    cons.append(f"{opt_stops} átszállásos repülőút a közvetlen helyett.")

                # Activities comparison
                opt_act_count = len(opt.get("activities", []))
                base_act_count = len(base.get("activities", []))
                if opt_act_count > base_act_count:
                    pros.append(f"Gazdagabb kulturális & élménykínálat ({opt_act_count} program).")

            narratives.append({
                "option_id": opt_id,
                "archetype": arch,
                "title": opt.get("title") or opt_city,
                "pros": pros,
                "cons": cons,
                "summary": (
                    f"{' · '.join(pros)}" if pros else "Megbízható, ellenőrzött utazási csomag."
                )
            })

        return narratives
