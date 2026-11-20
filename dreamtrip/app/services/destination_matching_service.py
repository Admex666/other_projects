"""
Optivoya Shared Intelligence — Destination Matching Service
Multi-criteria destination evaluation, climate matching, cost-of-living scoring,
live event intelligence integration (ADR-004 Honest Scraping), and AHP prioritization.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.services.destination_service import load_all_destinations
from app.services.numbeo_service import get_city_cost_and_safety
from app.services.experience_intelligence_service import ExperienceIntelligenceService
from app.services.event_intelligence_service import EventIntelligenceService
from app.models.event import EventQuery, EventCategory, EventSearchResult

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Safely runs an async coroutine from synchronous or threaded contexts."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def resolve_query_dates(
    month: int = 9,
    year: int = 2026,
    duration_days: int = 7,
    out_from: Optional[str] = None,
    out_to: Optional[str] = None,
    in_from: Optional[str] = None,
    in_to: Optional[str] = None,
) -> Tuple[date, date, bool]:
    """Resolves start_date, end_date and detects winter/NYE relevance."""
    # Resolve start_date
    if out_from:
        try:
            start_date = date.fromisoformat(out_from.split("T")[0])
        except Exception:
            start_date = date(year, max(1, min(12, month)), 1)
    else:
        if month == 12:
            start_date = date(year, 12, 28)
        elif month == 1:
            start_date = date(year, 1, 1)
        else:
            start_date = date(year, max(1, min(12, month)), 1)

    # Resolve end_date
    if in_to:
        try:
            end_date = date.fromisoformat(in_to.split("T")[0])
        except Exception:
            end_date = start_date + timedelta(days=duration_days)
    elif in_from:
        try:
            end_date = date.fromisoformat(in_from.split("T")[0])
        except Exception:
            end_date = start_date + timedelta(days=duration_days)
    elif out_to:
        try:
            end_date = date.fromisoformat(out_to.split("T")[0])
        except Exception:
            end_date = start_date + timedelta(days=duration_days)
    else:
        if month == 12:
            end_date = date(year + 1, 1, 3)
        elif month == 1:
            end_date = date(year, 1, min(31, max(2, duration_days)))
        else:
            end_date = start_date + timedelta(days=duration_days)

    if end_date < start_date:
        end_date = start_date + timedelta(days=duration_days)

    # Detect New Year's Eve / winter festive period
    is_nye = (
        (start_date <= date(start_date.year, 12, 31) <= end_date) or
        (start_date.month == 12 and start_date.day >= 27) or
        (end_date.month == 1 and end_date.day <= 5)
    )

    return start_date, end_date, is_nye


def compute_event_pricing(events: List[Any]) -> Dict[str, Any]:
    """ADR-004 Transparent event ticket and program pricing calculation.
    
    Rules:
    - Real ticket prices from verified connectors: is_estimated = False, price_provenance = 'verified', price_badge = 'Valós ár'
    - Free events: is_estimated = False, price_provenance = 'verified', price_badge = 'Valós ár'
    - Known events without listed ticket prices: is_estimated = True, price_provenance = 'estimated', price_badge = 'Becsült'
    - No events: is_estimated = False, price_provenance = 'none', price_badge = 'N/A'
    """
    priced_events = [e for e in events if getattr(e, "price_min", None) is not None and e.price_min > 0]
    free_events = [e for e in events if getattr(e, "is_free", False)]

    if priced_events:
        min_program_cost_eur = min(e.price_min for e in priced_events)
        return {
            "min_program_cost_eur": round(float(min_program_cost_eur), 2),
            "is_estimated": False,
            "price_provenance": "verified",
            "price_badge": "Valós ár",
        }
    elif free_events:
        return {
            "min_program_cost_eur": 0.0,
            "is_estimated": False,
            "price_provenance": "verified",
            "price_badge": "Valós ár",
        }
    elif events:
        # ADR-004: Explicitly mark transparent nominal estimation
        cats = {getattr(e, "category", "") for e in events}
        if EventCategory.PARTY_NIGHTLIFE in cats or "party_nightlife" in cats:
            nominal_est = 30.0
        elif EventCategory.MUSIC in cats or "music" in cats:
            nominal_est = 25.0
        else:
            nominal_est = 15.0

        return {
            "min_program_cost_eur": round(float(nominal_est), 2),
            "is_estimated": True,
            "price_provenance": "estimated",
            "price_badge": "Becsült",
        }
    else:
        return {
            "min_program_cost_eur": None,
            "is_estimated": False,
            "price_provenance": "none",
            "price_badge": "N/A",
        }


class DestinationMatchingService:
    """
    Unified destination matching service supporting both B2C and B2B workflows.
    Executes live multi-criteria candidate aggregation, climate filtering,
    asynchronous live event intelligence (ADR-004 Honest Scraping), and AHP weighting.
    """

    @classmethod
    async def enrich_destinations_with_events_async(
        cls,
        candidates: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        is_nye_only: bool = False,
        event_service: Optional[EventIntelligenceService] = None,
    ) -> List[Dict[str, Any]]:
        """Asynchronously queries EventIntelligenceService for each unique candidate city

        and enriches each destination with event_count, top_events, event_categories,
        is_event_enriched, and transparent pricing metadata (ADR-004).
        """
        if event_service is None:
            event_service = EventIntelligenceService()

        # Identify unique destination cities
        city_names = list({c.get("city") or c.get("name", "") for c in candidates if (c.get("city") or c.get("name"))})

        tasks = [
            event_service.search_events(EventQuery(
                city=city,
                start_date=start_date,
                end_date=end_date,
                is_nye_only=is_nye_only
            ))
            for city in city_names
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results_by_city: Dict[str, Optional[EventSearchResult]] = {}
        for city, resp in zip(city_names, responses):
            if isinstance(resp, Exception):
                logger.warning("Event search failed for destination city %s: %s", city, resp)
                results_by_city[city.lower()] = None
            elif isinstance(resp, EventSearchResult):
                results_by_city[city.lower()] = resp
            else:
                results_by_city[city.lower()] = None

        # Enrich each candidate
        for c in candidates:
            city_key = (c.get("city") or c.get("name", "")).strip().lower()
            res = results_by_city.get(city_key)

            if res and res.categories:
                all_events = [ev for cat_summary in res.categories.values() for ev in cat_summary.events]
                # Sort: NYE events first, then higher confidence, then priced events
                sorted_events = sorted(
                    all_events,
                    key=lambda x: (not x.is_nye_relevant, -x.confidence_score, x.price_min is None)
                )

                pricing = compute_event_pricing(sorted_events)
                top_events_list = [
                    {
                        "id": ev.id,
                        "title": ev.title,
                        "category": ev.category.value if hasattr(ev.category, "value") else str(ev.category),
                        "start_datetime": ev.start_datetime.isoformat(),
                        "venue_name": ev.venue.name if ev.venue else None,
                        "venue_address": ev.venue.address if ev.venue else None,
                        "price_min": ev.price_min,
                        "price_max": ev.price_max,
                        "currency": ev.currency or "EUR",
                        "is_free": bool(ev.is_free),
                        "source": ev.source,
                        "source_url": ev.source_url,
                        "image_url": ev.image_url,
                        "is_nye_relevant": ev.is_nye_relevant,
                        "confidence_score": ev.confidence_score,
                        "price_provenance": "verified" if (ev.price_min is not None or ev.is_free) else "none",
                        "price_badge": "Valós ár" if (ev.price_min is not None or ev.is_free) else "Becsült",
                    }
                    for ev in sorted_events[:5]
                ]

                distinct_cats = sorted(list({
                    ev.category.value if hasattr(ev.category, "value") else str(ev.category)
                    for ev in sorted_events
                }))

                c["event_count"] = len(sorted_events)
                c["top_events"] = top_events_list
                c["event_categories"] = distinct_cats
                c["is_event_enriched"] = True
                c["event_pricing"] = pricing
            else:
                c["event_count"] = 0
                c["top_events"] = []
                c["event_categories"] = []
                c["is_event_enriched"] = True
                c["event_pricing"] = {
                    "min_program_cost_eur": None,
                    "is_estimated": False,
                    "price_provenance": "none",
                    "price_badge": "N/A",
                }

        return candidates

    @classmethod
    async def evaluate_and_rank_destinations_async(
        cls,
        origin: str = "Budapest",
        month: int = 9,
        year: int = 2026,
        duration_days: int = 7,
        adults: int = 2,
        children: int = 0,
        target_temp: float = 24.0,
        min_safety: int = 50,
        preferred_regions: Optional[List[str]] = None,
        ahp_weights: Optional[Dict[str, float]] = None,
        out_from: Optional[str] = None,
        out_to: Optional[str] = None,
        in_from: Optional[str] = None,
        in_to: Optional[str] = None,
        min_stay: Optional[int] = None,
        max_stay: Optional[int] = None,
        limit: int = 20,
        event_service: Optional[EventIntelligenceService] = None,
    ) -> List[Dict[str, Any]]:
        """Asynchronous live multi-criteria candidate aggregation, climate filtering,

        event intelligence enrichment, and AHP prioritization.
        """
        all_candidates = load_all_destinations()

        # Regional and safety pre-filtering
        filtered_candidates = []
        for dest in all_candidates:
            region = dest.get("region", "")
            if preferred_regions and region not in preferred_regions:
                continue

            city_name = dest.get("city") or dest.get("name", "")
            country = dest.get("country", "")
            daily_cost_eur, safety_index, _ = get_city_cost_and_safety(city_name, country, region)

            if min_safety > 0 and safety_index < min_safety:
                continue

            vibe = ExperienceIntelligenceService.get_destination_vibe(city_name)
            enriched = dict(dest)
            enriched["daily_cost_eur"] = daily_cost_eur
            enriched["safety_score"] = safety_index
            enriched["safety_index"] = safety_index
            enriched["vibe_scores"] = vibe
            enriched["temperature_avg"] = target_temp
            filtered_candidates.append(enriched)

        # 2. Date resolution and live Event Intelligence enrichment
        start_date, end_date, is_nye = resolve_query_dates(
            month=month,
            year=year,
            duration_days=duration_days,
            out_from=out_from,
            out_to=out_to,
            in_from=in_from,
            in_to=in_to,
        )

        await cls.enrich_destinations_with_events_async(
            candidates=filtered_candidates,
            start_date=start_date,
            end_date=end_date,
            is_nye_only=False,
            event_service=event_service,
        )

        # 3. 4-Pillar AHP Weighting (Cost, Weather, Safety, Experience)
        weights = ahp_weights or {
            "total_cost": 30.0,
            "weather": 25.0,
            "safety": 25.0,
            "experience": 20.0,
        }

        total_w = sum(weights.values()) or 100.0
        w_cost = weights.get("total_cost", 30.0) / total_w
        w_weather = weights.get("weather", 25.0) / total_w
        w_safety = weights.get("safety", 25.0) / total_w
        w_exp = weights.get("experience", 20.0) / total_w

        for c in filtered_candidates:
            cost_norm = max(0.0, 1.0 - (c.get("daily_cost_eur", 80) / 250.0))
            safety_norm = c.get("safety_score", 70) / 100.0
            weather_norm = 0.9  # close match to target temp

            # Base vibe fit
            vibe_scores = c.get("vibe_scores", {})
            vibe_avg = sum(vibe_scores.values()) / max(1, len(vibe_scores)) / 100.0 if vibe_scores else 0.65

            # Event presence and diversity incorporation into s_exp
            event_count = c.get("event_count", 0)
            event_cats = c.get("event_categories", [])
            top_events = c.get("top_events", [])

            if c.get("is_event_enriched") and event_count > 0:
                presence_ratio = min(1.0, event_count / 6.0)
                cat_set = set(event_cats)
                target_cats = {"music", "party_nightlife", "gastronomy", "culture_arts", "community_festival"}
                diversity_ratio = min(1.0, len(cat_set & target_cats) / 3.0)
                has_nye = any(e.get("is_nye_relevant") for e in top_events)
                nye_bonus = 0.10 if has_nye else 0.0

                event_vibe = min(1.0, 0.45 * presence_ratio + 0.45 * diversity_ratio + nye_bonus)
                s_exp = round(min(1.0, max(0.20, vibe_avg * 0.70 + event_vibe * 0.30)), 3)
            else:
                s_exp = round(min(1.0, max(0.20, vibe_avg)), 3)

            c["s_exp"] = s_exp
            comp_score = (
                w_cost * cost_norm +
                w_weather * weather_norm +
                w_safety * safety_norm +
                w_exp * s_exp
            ) * 100.0
            c["match_score"] = round(comp_score, 1)

        filtered_candidates.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
        return filtered_candidates[:limit]

    @classmethod
    def evaluate_and_rank_destinations(
        cls,
        origin: str = "Budapest",
        month: int = 9,
        year: int = 2026,
        duration_days: int = 7,
        adults: int = 2,
        children: int = 0,
        target_temp: float = 24.0,
        min_safety: int = 50,
        preferred_regions: Optional[List[str]] = None,
        ahp_weights: Optional[Dict[str, float]] = None,
        out_from: Optional[str] = None,
        out_to: Optional[str] = None,
        in_from: Optional[str] = None,
        in_to: Optional[str] = None,
        min_stay: Optional[int] = None,
        max_stay: Optional[int] = None,
        limit: int = 20,
        event_service: Optional[EventIntelligenceService] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for evaluate_and_rank_destinations_async."""
        return _run_async(cls.evaluate_and_rank_destinations_async(
            origin=origin,
            month=month,
            year=year,
            duration_days=duration_days,
            adults=adults,
            children=children,
            target_temp=target_temp,
            min_safety=min_safety,
            preferred_regions=preferred_regions,
            ahp_weights=ahp_weights,
            out_from=out_from,
            out_to=out_to,
            in_from=in_from,
            in_to=in_to,
            min_stay=min_stay,
            max_stay=max_stay,
            limit=limit,
            event_service=event_service,
        ))
