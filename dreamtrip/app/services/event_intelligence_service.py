from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Set
from app.models.event import (
    EventItem,
    EventCategory,
    EventConfidence,
    EventStatus,
    EventQuery,
    EventSearchResult,
    CategoryEventSummary,
)
from app.services.events.base import BaseEventConnector
from app.services.events.resident_advisor_connector import ResidentAdvisorConnector
from app.services.events.eventbrite_connector import EventbriteConnector
from app.services.events.ticketmaster_connector import TicketmasterConnector
from app.services.events.local_agenda_connector import LocalAgendaConnector

logger = logging.getLogger(__name__)


SUPPORTED_WARM_WINTER_CITIES = [
    "Alicante",
    "Malaga",
    "Valencia",
    "Barcelona",
    "Sevilla",
    "Catania",
    "Valletta",
    "Paphos",
    "Lisbon",
]


class EventIntelligenceService:
    """Központi esemény-intelligencia szolgáltatás (Event Intelligence Engine).
    
    Megbízható, többforrásos eseményfelderítést végez a téli meleg célvárosokra,
    szigorú ADR-004 Honest Scraping szabályok betartásával (nincs fiktív adat,
    nincs évszám-hamisítás, minden elemhez valós forrás-URL tartozik).
    """

    def __init__(self, connectors: Optional[List[BaseEventConnector]] = None):
        if connectors is not None:
            self.connectors = connectors
        else:
            self.connectors = [
                TicketmasterConnector(),
                ResidentAdvisorConnector(),
                EventbriteConnector(),
                LocalAgendaConnector(),
            ]

    def get_supported_cities(self) -> List[str]:
        return list(SUPPORTED_WARM_WINTER_CITIES)

    async def search_events(self, query: EventQuery) -> EventSearchResult:
        """Események felkutatása adott városra és időszakra kategóriabontással és minőségbiztosítással."""
        city_name = query.city.strip()
        logger.info(
            "Event search initiated for %s between %s and %s (NYE only: %s)",
            city_name,
            query.start_date,
            query.end_date,
            query.is_nye_only,
        )

        # 1. Párhuzamos lekérés az aktív konnektorokból
        tasks = [
            conn.fetch_events(
                city=city_name,
                start_date=query.start_date,
                end_date=query.end_date,
                is_nye_only=query.is_nye_only,
            )
            for conn in self.connectors
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        all_events: List[EventItem] = []
        sources_used: Set[str] = set()
        warnings: List[str] = []

        for conn, resp in zip(self.connectors, responses):
            if isinstance(resp, Exception):
                msg = f"Connector '{conn.name}' failed: {str(resp)}"
                logger.error(msg)
                warnings.append(msg)
            elif isinstance(resp, list):
                if resp:
                    sources_used.add(conn.name)
                    all_events.extend(resp)
                else:
                    logger.debug("Connector '%s' returned 0 events for %s", conn.name, city_name)

        # 2. Szigorú Honest Scraping (ADR-004) és minőségi szűrők
        valid_events = self._apply_honest_validation(
            events=all_events,
            query=query,
            warnings=warnings,
        )

        # 3. Deduplikáció
        deduped_events = self._deduplicate_events(valid_events)

        # 4. Kategóriák szerinti szűrés és csoportosítás
        categorized_dict = self._group_by_categories(
            events=deduped_events,
            allowed_categories=query.categories,
            limit_per_category=query.limit_per_category,
        )

        total_count = sum(c.count for c in categorized_dict.values())

        if total_count == 0 and not warnings:
            warnings.append(
                f"No verified events found for {city_name} in the interval {query.start_date}..{query.end_date} obeying ADR-004."
            )

        return EventSearchResult(
            city=city_name,
            query_start_date=query.start_date,
            query_end_date=query.end_date,
            total_events=total_count,
            categories=categorized_dict,
            sources_used=sorted(list(sources_used)),
            honest_validation_passed=True,
            errors_or_warnings=warnings,
        )

    def _apply_honest_validation(
        self,
        events: List[EventItem],
        query: EventQuery,
        warnings: List[str]
    ) -> List[EventItem]:
        """ADR-004 Honest Scraping szabályok kikényszerítése:
        - Nincs fiktív adat: URL kötelező, valódi hosttal
        - Nincs elavult vagy jövőbeli intervallumon kívüli esemény
        - Minimális confidence_score elérése
        - NYE szűrés ha query.is_nye_only
        """
        filtered: List[EventItem] = []

        for ev in events:
            # Dátum érvényesség
            ev_date = ev.start_datetime.date()
            if not (query.start_date <= ev_date <= query.end_date):
                # Régi vagy intervallumon kívüli esemény kiszűrése
                continue

            # Forrás URL megléte
            if not ev.source_url or not ev.source_url.startswith("http"):
                continue

            # Cím integritása
            if not ev.title or len(ev.title.strip()) < 2:
                continue

            # Confidence küszöb
            if ev.confidence_score < query.min_confidence_score:
                continue

            # NYE szűrés
            if query.is_nye_only and not ev.is_nye_relevant:
                continue

            filtered.append(ev)

        return filtered

    def _deduplicate_events(self, events: List[EventItem]) -> List[EventItem]:
        """Események deduplikációja cím-normalizálás és dátumegyezés alapján."""
        deduped: Dict[str, EventItem] = {}

        for ev in events:
            # Normalizált kulcs generálása
            title_clean = "".join(ch.lower() for ch in ev.title if ch.isalnum() or ch.isspace())
            date_key = ev.start_datetime.date().isoformat()
            key = f"{date_key}_{title_clean[:35]}"

            if key not in deduped:
                deduped[key] = ev
            else:
                existing = deduped[key]
                # Ha az új elem megbízhatóbb (magasabb confidence_score), cseréljük
                if ev.confidence_score > existing.confidence_score:
                    deduped[key] = ev
                # Ha az meglévőnek nincs ára, de az újnak van, átvesszük
                elif existing.price_min is None and ev.price_min is not None:
                    existing.price_min = ev.price_min
                    existing.price_max = ev.price_max

        # Időrendi rendezés
        sorted_events = sorted(deduped.values(), key=lambda x: x.start_datetime)
        return sorted_events

    def _group_by_categories(
        self,
        events: List[EventItem],
        allowed_categories: Optional[List[EventCategory]] = None,
        limit_per_category: int = 15,
    ) -> Dict[str, CategoryEventSummary]:
        """Események kategóriákba csoportosítása."""
        grouped: Dict[EventCategory, List[EventItem]] = {cat: [] for cat in EventCategory}

        for ev in events:
            if allowed_categories and ev.category not in allowed_categories:
                continue
            grouped[ev.category].append(ev)

        result: Dict[str, CategoryEventSummary] = {}
        for cat in EventCategory:
            cat_events = grouped[cat][:limit_per_category]
            result[cat.value] = CategoryEventSummary(
                category=cat,
                count=len(cat_events),
                events=cat_events,
            )

        return result
