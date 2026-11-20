from __future__ import annotations

import logging
import httpx
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
from typing import List, Optional, Dict
from app.models.event import EventItem, EventCategory, EventConfidence, EventStatus, EventVenue
from app.services.events.base import BaseEventConnector

logger = logging.getLogger(__name__)

# Megbízható helyi kulturális és turisztikai naptár URL-ek
LOCAL_AGENDA_TARGETS = {
    "valencia": {
        "name": "Visit Valencia Agenda",
        "url": "https://www.visitvalencia.com/en/agenda-valencia",
        "country": "Spain"
    },
    "lisbon": {
        "name": "Viral Agenda Lisboa",
        "url": "https://www.viralagenda.com/pt/lisboa",
        "country": "Portugal"
    },
    "barcelona": {
        "name": "Barcelona Turisme Agenda",
        "url": "https://www.barcelonaturisme.com/agenda",
        "country": "Spain"
    }
}


class LocalAgendaConnector(BaseEventConnector):
    """Helyi turisztikai portálok és városi kulturális naptárak közvetlen discovery motorja."""

    def __init__(self):
        super().__init__(name="local_agenda")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8,pt;q=0.8",
        }

    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False
    ) -> List[EventItem]:
        city_clean = city.strip().lower()
        target = LOCAL_AGENDA_TARGETS.get(city_clean)
        if not target:
            return []

        results: List[EventItem] = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target["url"], headers=self.headers)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                # Parse JSON-LD scripts if present
                for s in soup.find_all("script", type="application/ld+json"):
                    if not s.string:
                        continue
                    try:
                        data = json.loads(s.string)
                        raw_items = []
                        if isinstance(data, dict):
                            if data.get("@type") == "Event":
                                raw_items.append(data)
                            elif data.get("@type") == "ItemList":
                                raw_items.extend([el.get("item", {}) for el in data.get("itemListElement", []) if isinstance(el, dict)])
                        elif isinstance(data, list):
                            for d in data:
                                if isinstance(d, dict) and d.get("@type") == "Event":
                                    raw_items.append(d)

                        for item_data in raw_items:
                            title = (item_data.get("name") or "").strip()
                            source_url = item_data.get("url") or target["url"]
                            start_str = item_data.get("startDate")
                            if not title or not start_str:
                                continue

                            try:
                                if "T" in start_str:
                                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                                else:
                                    parts = start_str.split("-")
                                    start_dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]), 19, 0, 0)
                            except Exception:
                                continue

                            if not self.is_within_range(start_dt, start_date, end_date):
                                continue

                            is_nye = self.detect_nye_relevance(title, None, start_dt)
                            if is_nye_only and not is_nye:
                                continue

                            category = self.classify_category(title, None, default=EventCategory.CULTURE_ARTS)
                            tags = self.extract_tags(title, None)

                            venue = EventVenue(
                                name=f"Civic Venue {city.title()}",
                                address=None,
                                city=city.title(),
                                country=target["country"]
                            )

                            ev_id = f"ev_agenda_{abs(hash(title + str(start_dt))) % 10000000}"
                            item = EventItem(
                                id=ev_id,
                                title=title,
                                description=f"Curated official city agenda item from {target['name']}",
                                city=city.title(),
                                venue=venue,
                                start_datetime=start_dt,
                                end_datetime=None,
                                category=category,
                                tags=tags,
                                price_min=None,
                                price_max=None,
                                currency="EUR",
                                is_free=None,
                                source="local_agenda",
                                source_url=source_url,
                                image_url=item_data.get("image"),
                                confidence=EventConfidence.COMMUNITY_CURATED,
                                confidence_score=0.75,
                                status=EventStatus.CONFIRMED,
                                is_nye_relevant=is_nye
                            )
                            results.append(item)
                    except Exception:
                        continue

        except Exception as e:
            logger.debug("Local agenda discovery skipped for %s: %s", city, e)

        return results
