from __future__ import annotations

import os
import logging
import httpx
from datetime import datetime, date
from typing import List, Optional
from app.models.event import EventItem, EventCategory, EventConfidence, EventStatus, EventVenue
from app.services.events.base import BaseEventConnector

logger = logging.getLogger(__name__)


class TicketmasterConnector(BaseEventConnector):
    """Ticketmaster Discovery API v2 integráció megerősített koncert-, színház- és fesztiváladatokhoz."""

    def __init__(self):
        super().__init__(name="ticketmaster")
        self.api_key = os.getenv("TICKETMASTER_API_KEY", "").strip()
        self.endpoint = "https://app.ticketmaster.com/discovery/v2/events.json"

    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False
    ) -> List[EventItem]:
        if not self.api_key:
            logger.info("Ticketmaster Discovery: TICKETMASTER_API_KEY not configured. Skipping source.")
            return []

        start_iso = f"{start_date.isoformat()}T00:00:00Z"
        end_iso = f"{end_date.isoformat()}T23:59:59Z"

        params = {
            "apikey": self.api_key,
            "city": city,
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "size": 50,
            "sort": "date,asc"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 401 or resp.status_code == 403:
                    logger.warning("Ticketmaster API key invalid or unauthorized: %s", resp.status_code)
                    return []
                if resp.status_code != 200:
                    logger.warning("Ticketmaster API returned status %s for %s", resp.status_code, city)
                    return []

                data = resp.json()
                raw_events = data.get("_embedded", {}).get("events", [])
                results: List[EventItem] = []

                for ev in raw_events:
                    title = (ev.get("name") or "").strip()
                    source_url = ev.get("url") or ""
                    if not title or not source_url:
                        continue

                    dates_info = ev.get("dates", {})
                    start_str = dates_info.get("start", {}).get("dateTime") or dates_info.get("start", {}).get("localDate")
                    if not start_str:
                        continue

                    try:
                        if "T" in start_str:
                            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        else:
                            start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                    except Exception:
                        continue

                    if not self.is_within_range(start_dt, start_date, end_date):
                        continue

                    is_nye = self.detect_nye_relevance(title, None, start_dt)
                    if is_nye_only and not is_nye:
                        continue

                    # Venues
                    venues = ev.get("_embedded", {}).get("venues", [])
                    venue_name = f"Venue {city.title()}"
                    venue_addr = None
                    lat, lon = None, None
                    if venues:
                        v0 = venues[0]
                        venue_name = v0.get("name") or venue_name
                        venue_addr = v0.get("address", {}).get("line1")
                        loc_obj = v0.get("location", {})
                        if loc_obj:
                            try:
                                lat = float(loc_obj.get("latitude"))
                                lon = float(loc_obj.get("longitude"))
                            except Exception:
                                pass

                    venue = EventVenue(
                        name=venue_name,
                        address=venue_addr,
                        city=city.title(),
                        country=None,
                        latitude=lat,
                        longitude=lon
                    )

                    # Árak
                    price_ranges = ev.get("priceRanges", [])
                    p_min, p_max, curr = None, None, "EUR"
                    if price_ranges:
                        p_min = price_ranges[0].get("min")
                        p_max = price_ranges[0].get("max")
                        curr = price_ranges[0].get("currency", "EUR")

                    # Kép
                    img_url = None
                    images = ev.get("images", [])
                    if images:
                        img_url = images[0].get("url")

                    # Kategória
                    category = self.classify_category(title, None, default=EventCategory.MUSIC)
                    tags = self.extract_tags(title, None)

                    item = EventItem(
                        id=f"ev_tm_{ev.get('id')}",
                        title=title,
                        description=f"Ticketmaster verified event in {city.title()}",
                        city=city.title(),
                        venue=venue,
                        start_datetime=start_dt,
                        end_datetime=None,
                        category=category,
                        tags=tags,
                        price_min=p_min,
                        price_max=p_max,
                        currency=curr,
                        is_free=False,
                        source="ticketmaster",
                        source_url=source_url,
                        image_url=img_url,
                        confidence=EventConfidence.VERIFIED_API,
                        confidence_score=0.95,
                        status=EventStatus.CONFIRMED,
                        is_nye_relevant=is_nye
                    )
                    results.append(item)

                return results

        except Exception as e:
            logger.error("Ticketmaster connector exception: %s", e)
            return []
