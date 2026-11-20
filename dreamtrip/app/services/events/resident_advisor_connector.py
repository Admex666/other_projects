from __future__ import annotations

import logging
import httpx
from datetime import datetime, date
from typing import List, Optional, Dict
from app.models.event import EventItem, EventCategory, EventConfidence, EventStatus, EventVenue
from app.services.events.base import BaseEventConnector

logger = logging.getLogger(__name__)

RA_CITY_AREAS: Dict[str, int] = {
    "barcelona": 20,
    "lisbon": 53,
    "lisszabon": 53,
    "valencia": 607,
    "malaga": 608,
    "málaga": 608,
    "alicante": 613,
    "malta": 164,
    "valletta": 164,
    "cyprus": 197,
    "paphos": 197,
    "páfosz": 197,
}

GRAPHQL_QUERY = """
query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $pageSize: Int) {
  eventListings(filters: $filters, pageSize: $pageSize) {
    totalResults
    data {
      id
      listingDate
      event {
        id
        title
        startTime
        endTime
        contentUrl
        flyerFront
        venue {
          id
          name
          address
        }
        cost
      }
    }
  }
}
"""


class ResidentAdvisorConnector(BaseEventConnector):
    """Resident Advisor (RA.co) esemény-integráció a partikra, klubokra és elektronikus zenei eseményekre."""

    def __init__(self):
        super().__init__(name="resident_advisor")
        self.endpoint = "https://ra.co/graphql"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "https://ra.co/events",
        }

    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False
    ) -> List[EventItem]:
        city_clean = city.strip().lower()
        area_id = RA_CITY_AREAS.get(city_clean)
        if not area_id:
            logger.info("Resident Advisor: no area mapping for city '%s', skipping", city)
            return []

        variables = {
            "filters": {
                "areas": {"eq": area_id},
                "listingDate": {
                    "gte": start_date.isoformat(),
                    "lte": end_date.isoformat()
                }
            },
            "pageSize": 50
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    self.endpoint,
                    json={"query": GRAPHQL_QUERY, "variables": variables},
                    headers=self.headers
                )
                if resp.status_code != 200:
                    logger.warning("RA GraphQL returned status %s for %s", resp.status_code, city)
                    return []

                payload = resp.json()
                listings = payload.get("data", {}).get("eventListings", {}).get("data", [])

                results: List[EventItem] = []
                for entry in listings:
                    ev_data = entry.get("event")
                    if not ev_data:
                        continue

                    title = (ev_data.get("title") or "").strip()
                    if not title:
                        continue

                    raw_start = ev_data.get("startTime") or entry.get("listingDate")
                    if not raw_start:
                        continue

                    try:
                        # Parse ISO datetime
                        start_dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
                    except Exception:
                        continue

                    # Szigorú Honest Scraping ellenőrzés
                    if not self.is_within_range(start_dt, start_date, end_date):
                        continue

                    raw_end = ev_data.get("endTime")
                    end_dt: Optional[datetime] = None
                    if raw_end:
                        try:
                            end_dt = datetime.fromisoformat(raw_end.replace("Z", "+00:00"))
                        except Exception:
                            end_dt = None

                    # NYE szűrés
                    is_nye = self.detect_nye_relevance(title, None, start_dt)
                    if is_nye_only and not is_nye:
                        continue

                    # Venue adatok
                    v_info = ev_data.get("venue") or {}
                    venue = EventVenue(
                        name=v_info.get("name") or f"Venue {city.title()}",
                        address=v_info.get("address"),
                        city=city.title(),
                        country=None
                    )

                    # Kategória besorolás (RA alapból zene / party)
                    category = self.classify_category(title, None, default=EventCategory.PARTY_NIGHTLIFE)
                    tags = self.extract_tags(title, None)
                    if "electronic" not in tags:
                        tags.append("electronic")

                    # Ár kinyerése
                    cost_str = str(ev_data.get("cost") or "").strip()
                    price_val: Optional[float] = None
                    try:
                        digits = "".join(ch for ch in cost_str if ch.isdigit() or ch == ".")
                        if digits:
                            price_val = float(digits)
                    except Exception:
                        price_val = None

                    content_url = ev_data.get("contentUrl") or ""
                    source_url = f"https://ra.co{content_url}" if content_url.startswith("/") else (content_url or "https://ra.co")

                    item = EventItem(
                        id=f"ev_ra_{ev_data.get('id')}",
                        title=title,
                        description=f"Resident Advisor listing at {venue.name}",
                        city=city.title(),
                        venue=venue,
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                        category=category,
                        tags=tags,
                        price_min=price_val,
                        price_max=price_val,
                        currency="EUR",
                        is_free=False,
                        source="resident_advisor",
                        source_url=source_url,
                        image_url=ev_data.get("flyerFront"),
                        confidence=EventConfidence.SCRAPED_STRUCTURED,
                        confidence_score=0.90,
                        status=EventStatus.CONFIRMED,
                        is_nye_relevant=is_nye
                    )
                    results.append(item)

                return results

        except Exception as e:
            logger.error("RA connector exception for %s: %s", city, e)
            return []
