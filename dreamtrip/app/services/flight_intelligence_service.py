"""
Optivoya Shared Intelligence — Flight Intelligence Service
Unified flight search, carrier aggregation, Kiwi API integration, and PROMETHEE II ranking service.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from app.scrapers import scraper
from app.services.promethee_engine import PrometheeEngine
from app.services.exchange_service import get_eur_huf_rate


class FlightIntelligenceService:
    """
    Unified flight intelligence service supporting both B2C Master Planner and B2B Advisor Workspace.
    Handles Kiwi API querying, multi-segment parsing, and PROMETHEE II ranking.
    """

    @classmethod
    def search_and_rank_flights(
        cls,
        origin: str,
        destination: str,
        out_date: str,
        in_date: str,
        adults: int = 2,
        direct_only: bool = False,
        max_stops: int = 1,
        departure_hour_pref: int = 0,
        has_dep_pref: bool = False,
        max_duration_h: float = 0.0,
        promethee_params: Optional[Dict[str, Any]] = None,
        ahp_weights: Optional[Dict[str, float]] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Executes live flight search via Kiwi and applies PROMETHEE II outranking.
        """
        tokens = scraper.get_kiwi_tokens()

        out_df = scraper.search_flights_by_city_name_v2(
            origin_name=origin,
            destination_name=destination,
            tokens=tokens,
            date_from=out_date,
            date_to=out_date,
            adults=adults,
            limit=limit * 2
        )
        in_df = scraper.search_flights_by_city_name_v2(
            origin_name=destination,
            destination_name=origin,
            tokens=tokens,
            date_from=in_date,
            date_to=in_date,
            adults=adults,
            limit=limit * 2
        )

        if out_df is not None and not out_df.empty and in_df is not None and not in_df.empty:
            comb_df = scraper.create_return_combinations(out_df, in_df)
            flight_candidates = comb_df.to_dict(orient="records") if comb_df is not None and not comb_df.empty else out_df.to_dict(orient="records")
        elif out_df is not None and not out_df.empty:
            flight_candidates = out_df.to_dict(orient="records")
        else:
            return []

        # Convert to list of dicts
        filtered_candidates = []
        for fl in flight_candidates:
            out_stops = int(fl.get("out_stops", 0) or 0)
            in_stops = int(fl.get("in_stops", 0) or 0)
            total_stops = out_stops + in_stops

            if direct_only and total_stops > 0:
                continue

            if max_stops > 0 and (out_stops > max_stops or in_stops > max_stops):
                continue

            out_dur = float(fl.get("out_duration_h", 0.0) or 0.0)
            in_dur = float(fl.get("in_duration_h", 0.0) or 0.0)
            total_dur = out_dur + in_dur

            if max_duration_h > 0 and out_dur > max_duration_h:
                continue

            price_huf = float(fl.get("price_huf", 0.0) or 0.0)

            enriched = dict(fl)
            enriched["total_price_huf"] = price_huf
            enriched["price_total_huf"] = price_huf
            enriched["total_duration_h"] = total_dur
            enriched["stops"] = total_stops
            enriched["out_stops"] = out_stops
            enriched["in_stops"] = in_stops
            filtered_candidates.append(enriched)

        if not filtered_candidates:
            return []

        # Configure PROMETHEE Criteria
        prom_cfg = promethee_params or {}
        price_cfg = prom_cfg.get("price", {"type": 5, "q": 5000, "p": 35000})
        dur_cfg = prom_cfg.get("duration", {"type": 5, "q": 0.5, "p": 3.0})

        criteria_configs = {
            "total_price_huf": {
                "type": price_cfg.get("type", 5),
                "q": price_cfg.get("q", 5000),
                "p": price_cfg.get("p", 35000),
                "direction": "min"
            },
            "total_duration_h": {
                "type": dur_cfg.get("type", 5),
                "q": dur_cfg.get("q", 0.5),
                "p": dur_cfg.get("p", 3.0),
                "direction": "min"
            },
            "stops": {
                "type": 3,
                "q": 0.0,
                "p": 2.0,
                "direction": "min"
            }
        }

        # Weights
        weights = ahp_weights or {"total_price_huf": 40.0, "total_duration_h": 35.0, "stops": 25.0}

        ranked_flights = PrometheeEngine.rank_alternatives(
            alternatives=filtered_candidates,
            criteria_configs=criteria_configs,
            criteria_weights=weights
        )

        return ranked_flights[:limit]
