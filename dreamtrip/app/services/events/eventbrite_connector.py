from __future__ import annotations

import logging
import json
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import List, Optional, Dict
from app.models.event import EventItem, EventCategory, EventConfidence, EventStatus, EventVenue
from app.services.events.base import BaseEventConnector

logger = logging.getLogger(__name__)

EVENTBRITE_CITY_SLUGS: Dict[str, str] = {
    "barcelona": "spain--barcelona",
    "valencia": "spain--valencia",
    "malaga": "spain--malaga",
    "málaga": "spain--malaga",
    "alicante": "spain--alicante",
    "seville": "spain--seville",
    "sevilla": "spain--seville",
    "lisbon": "portugal--lisbon",
    "lisszabon": "portugal--lisbon",
    "catania": "italy--catania",
    "valletta": "malta--valletta",
    "malta": "malta--valletta",
    "paphos": "cyprus--paphos",
    "páfosz": "cyprus--paphos",
}


class EventbriteConnector(BaseEventConnector):
    """Eventbrite nyílt Schema.org JSON-LD eseménykinyerő valós, ellenőrizhető URL-ekkel."""

    def __init__(self):
        super().__init__(name="eventbrite")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        }

    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False
    ) -> List[EventItem]:
        city_clean = city.strip().lower()
        slug = EVENTBRITE_CITY_SLUGS.get(city_clean)
        if not slug:
            logger.info("Eventbrite: no slug for city '%s', skipping", city)
            return []

        # Tervezett query utak: NYE keresés esetén new-years-eve--events, egyébként all-events és music
        query_paths = []
        if is_nye_only or (start_date.month == 12 and end_date.month == 1):
            query_paths.append("new-years-eve--events")
            query_paths.append("party--events")
        else:
            query_paths.append("all-events")
            query_paths.append("music--events")

        collected_events: Dict[str, EventItem] = {}

        async with httpx.AsyncClient(timeout=14.0, follow_redirects=True) as client:
            for q_path in query_paths:
                url = f"https://www.eventbrite.com/d/{slug}/{q_path}/"
                try:
                    resp = await client.get(url, headers=self.headers)
                    if resp.status_code != 200:
                        logger.warning("Eventbrite returned status %s for url %s", resp.status_code, url)
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    scripts = soup.find_all("script", type="application/ld+json")

                    for s in scripts:
                        if not s.string:
                            continue
                        try:
                            data = json.loads(s.string)
                        except Exception:
                            continue

                        # ItemList keresése
                        items = []
                        if isinstance(data, dict) and data.get("@type") == "ItemList":
                            items = data.get("itemListElement", [])
                        elif isinstance(data, list):
                            for d in data:
                                if isinstance(d, dict) and d.get("@type") == "ItemList":
                                    items.extend(d.get("itemListElement", []))

                        for elem in items:
                            item_obj = elem.get("item", {}) if isinstance(elem, dict) else {}
                            if not item_obj:
                                continue

                            title = (item_obj.get("name") or "").strip()
                            source_url = item_obj.get("url") or ""
                            raw_start = item_obj.get("startDate")

                            if not title or not source_url or not raw_start:
                                continue

                            # Dátum parse-olás (ISO datetime vagy YYYY-MM-DD)
                            try:
                                if "T" in raw_start:
                                    start_dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
                                else:
                                    d_parts = raw_start.split("-")
                                    start_dt = datetime(int(d_parts[0]), int(d_parts[1]), int(d_parts[2]), 20, 0, 0)
                            except Exception:
                                continue

                            # Szigorú ADR-004 intervallum szűrés! Tilos régi vagy intervallumon kívüli esemény
                            if not self.is_within_range(start_dt, start_date, end_date):
                                continue

                            is_nye = self.detect_nye_relevance(title, None, start_dt)
                            if is_nye_only and not is_nye:
                                continue

                            # Venue adatok
                            loc = item_obj.get("location", {})
                            venue_name = loc.get("name") if isinstance(loc, dict) else f"Event Venue {city.title()}"
                            venue_addr = None
                            if isinstance(loc, dict) and isinstance(loc.get("address"), dict):
                                addr_obj = loc["address"]
                                venue_addr = f"{addr_obj.get('streetAddress', '')}, {addr_obj.get('addressLocality', '')}".strip(", ")

                            venue = EventVenue(
                                name=venue_name or f"Venue {city.title()}",
                                address=venue_addr,
                                city=city.title(),
                                country=None
                            )

                            category = self.classify_category(title, None, default=EventCategory.PARTY_NIGHTLIFE if is_nye else EventCategory.CULTURE_ARTS)
                            tags = self.extract_tags(title, None)

                            # Eventbrite egyedi azonosító kinyerése az URL végéből
                            ev_id = "ev_eb_" + source_url.rstrip("/").split("-")[-1]

                            event_item = EventItem(
                                id=ev_id,
                                title=title,
                                description=f"Eventbrite listing in {city.title()}",
                                city=city.title(),
                                venue=venue,
                                start_datetime=start_dt,
                                end_datetime=None,
                                category=category,
                                tags=tags,
                                price_min=None,
                                price_max=None,
                                currency="EUR",
                                is_free=False,
                                source="eventbrite",
                                source_url=source_url,
                                image_url=item_obj.get("image"),
                                confidence=EventConfidence.SCRAPED_STRUCTURED,
                                confidence_score=0.85,
                                status=EventStatus.CONFIRMED,
                                is_nye_relevant=is_nye
                            )

                            if event_item.id not in collected_events:
                                collected_events[event_item.id] = event_item

                except Exception as e:
                    logger.error("Eventbrite scraper error for %s on %s: %s", city, q_path, e)

        return list(collected_events.values())
