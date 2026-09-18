"""
Optivoya Shared Intelligence — Accommodation Intelligence Service
Unified accommodation search, Cozycozy scraper integration, filter enforcement, and multi-criteria accommodation scoring.
"""

from typing import List, Dict, Any, Optional
from app.scrapers.accommodation_scraper import get_all_stays, parse_accommodation_results
from app.services.promethee_engine import PrometheeEngine


class AccommodationIntelligenceService:
    """
    Unified accommodation service supporting both B2C Master Planner and B2B Advisor Workspace.
    Handles Cozycozy scraping, star/rating filtering, and stay prioritization.
    """

    @classmethod
    def search_and_rank_stays(
        cls,
        city: str,
        country: str,
        checkin: str,
        checkout: str,
        adults: int = 2,
        min_stars: int = 3,
        min_rating: float = 7.5,
        hotel_types: Optional[List[str]] = None,
        breakfast: bool = False,
        amenities: Optional[List[str]] = None,
        stay_weights: Optional[Dict[str, float]] = None,
        promethee_params: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Executes accommodation search and ranks candidates according to criteria.
        """
        # Fetch stays via scraper
        raw_stays = get_all_stays(
            city=city,
            country=country,
            start_date=checkin,
            end_date=checkout,
            adults=adults,
            children=0,
            min_rating=min_rating,
            accommodation_types=hotel_types,
            breakfast=breakfast,
            amenities=amenities or []
        )

        if not raw_stays:
            return []

        # Filter and normalize
        candidates = []
        for s in raw_stays:
            stars = int(s.get("stars", 0) or 0)
            if min_stars > 0 and stars > 0 and stars < min_stars:
                continue

            rating_score = float(s.get("rating_score", 0.0) or 0.0)
            # Normalize 100-scale ratings to 10-scale
            if rating_score > 10.0:
                rating_score = rating_score / 10.0

            if min_rating > 0 and rating_score > 0 and rating_score < min_rating:
                continue

            price_total = float(s.get("price_total_huf", 0.0) or s.get("price_huf", 0.0) or 0.0)

            enriched = dict(s)
            enriched["price_total_huf"] = price_total
            enriched["rating_normalized"] = rating_score
            enriched["stars_normalized"] = stars
            candidates.append(enriched)

        if not candidates:
            return []

        # Configure Multi-criteria ranking via PrometheeEngine
        prom_cfg = promethee_params or {}
        price_cfg = prom_cfg.get("price", {"type": 5, "q": 3000, "p": 15000})
        rating_cfg = prom_cfg.get("rating", {"type": 5, "q": 0.4, "p": 1.5})

        criteria_configs = {
            "price_total_huf": {
                "type": price_cfg.get("type", 5),
                "q": price_cfg.get("q", 3000),
                "p": price_cfg.get("p", 15000),
                "direction": "min"
            },
            "rating_normalized": {
                "type": rating_cfg.get("type", 5),
                "q": rating_cfg.get("q", 0.4),
                "p": rating_cfg.get("p", 1.5),
                "direction": "max"
            },
            "stars_normalized": {
                "type": 3,
                "q": 0.0,
                "p": 2.0,
                "direction": "max"
            }
        }

        weights = stay_weights or {"price_total_huf": 35.0, "rating_normalized": 40.0, "stars_normalized": 25.0}

        ranked_stays = PrometheeEngine.rank_alternatives(
            alternatives=candidates,
            criteria_configs=criteria_configs,
            criteria_weights=weights
        )

        return ranked_stays[:limit]
