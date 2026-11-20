from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Tuple
from app.models.event import EventItem, EventCategory, EventConfidence, EventStatus, EventVenue


NYE_KEYWORDS = [
    "nye", "new year", "new years", "new year's eve", "silvester", "szilveszter",
    "nochevieja", "fin de año", "fin de ano", "ano nuevo", "año nuevo",
    "reveillon", "réveillon", "capodanno", "countdown", "san silvestre"
]

CATEGORY_PATTERNS = [
    (
        EventCategory.PARTY_NIGHTLIFE,
        [
            r"\bparty\b", r"\bclub\b", r"\bdj\b", r"\brave\b", r"\bnightlife\b",
            r"\bfiesta\b", r"\bbar crawl\b", r"\bpub crawl\b", r"\btechno\b",
            r"\bdisco\b", r"\bnye party\b", r"\bnochevieja\b", r"\breveillon\b"
        ]
    ),
    (
        EventCategory.MUSIC,
        [
            r"\bconcert\b", r"\blive music\b", r"\bkoncert\b", r"\borchestra\b",
            r"\bjazz\b", r"\brock\b", r"\bacoustic\b", r"\bsinger\b", r"\bband\b",
            r"\bsymphon", r"\bopera\b", r"\bflamenco\b", r"\bfestival\b"
        ]
    ),
    (
        EventCategory.GASTRONOMY,
        [
            r"\bgastro\b", r"\bfood\b", r"\bwine\b", r"\btasting\b", r"\bdinner\b",
            r"\bcena\b", r"\btapas\b", r"\bcava\b", r"\bculinary\b", r"\bbrunch\b",
            r"\bmarket\b", r"\bdegustation\b", r"\bgala dinner\b"
        ]
    ),
    (
        EventCategory.CULTURE_ARTS,
        [
            r"\bart\b", r"\bmuseum\b", r"\bexhibition\b", r"\btheatre\b", r"\btheater\b",
            r"\bteatro\b", r"\bopera\b", r"\bballet\b", r"\bguided tour\b", r"\bhistory\b",
            r"\bculture\b", r"\bcinema\b", r"\bcircus\b", r"\bperformance\b"
        ]
    ),
    (
        EventCategory.COMMUNITY_FESTIVAL,
        [
            r"\bparade\b", r"\bfireworks\b", r"\blights\b", r"\bferia\b", r"\bmarket\b",
            r"\bplaza\b", r"\bstreet festival\b", r"\bcarol\b", r"\bchristmas market\b",
            r"\bcabalgata\b"
        ]
    ),
    (
        EventCategory.SPORTS_WELLNESS,
        [
            r"\brun\b", r"\bmarathon\b", r"\byoga\b", r"\bfitness\b", r"\bwellness\b",
            r"\bsan silvestre\b", r"\brace\b", r"\bhike\b", r"\bcycling\b"
        ]
    ),
]


class BaseEventConnector(ABC):
    """Absztrakt alaposztály a külső eseményforrások integrációjához (ADR-004 kompatibilis)."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False
    ) -> List[EventItem]:
        """Események letöltése és átalakítása belső EventItem modellre."""
        pass

    @staticmethod
    def is_within_range(event_dt: datetime, start_date: date, end_date: date) -> bool:
        """Szigorú dátumintervallum ellenőrzés (ADR-004 elavult/jövőbeli túllógás kizárása)."""
        ev_date = event_dt.date() if isinstance(event_dt, datetime) else event_dt
        return start_date <= ev_date <= end_date

    @staticmethod
    def detect_nye_relevance(title: str, description: Optional[str], event_dt: datetime) -> bool:
        """Detektálja, hogy az esemény kifejezetten a szilveszteri ünnepkörhöz tartozik-e."""
        ev_date = event_dt.date() if isinstance(event_dt, datetime) else event_dt
        # Dec 31 és Jan 1 automatikusan NYE releváns
        if (ev_date.month == 12 and ev_date.day == 31) or (ev_date.month == 1 and ev_date.day == 1):
            return True
        
        text = f"{title} {description or ''}".lower()
        return any(keyword in text for keyword in NYE_KEYWORDS)

    @staticmethod
    def classify_category(title: str, description: Optional[str] = None, default: EventCategory = EventCategory.OTHER) -> EventCategory:
        """Szövegelemzés alapú kategóriabesorolás regex minták illesztésével."""
        combined_text = f"{title} {description or ''}".lower()
        
        for category, patterns in CATEGORY_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return category
        
        return default

    @staticmethod
    def extract_tags(title: str, description: Optional[str] = None) -> List[str]:
        """Hasznos címkék kinyerése a szövegből."""
        text = f"{title} {description or ''}".lower()
        found_tags = set()
        
        # Check NYE
        if any(k in text for k in NYE_KEYWORDS):
            found_tags.add("nye")
            found_tags.add("new-years-eve")
        
        # Music genres
        genres = ["techno", "house", "electronic", "rock", "jazz", "indie", "flamenco", "latin", "hip hop", "r&b", "pop"]
        for g in genres:
            if re.search(rf"\b{g}\b", text):
                found_tags.add(g.replace(" ", "-"))

        # Gastro
        if any(k in text for k in ["tapas", "wine", "dinner", "cocktail", "brunch"]):
            found_tags.add("gastronomy")

        return sorted(list(found_tags))
