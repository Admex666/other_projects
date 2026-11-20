"""
Optivoya Test Suite — Destination Matching & Event Intelligence Integration
Tests the live integration of EventIntelligenceService into DestinationMatchingService,
4-pillar AHP scoring (s_exp), ADR-004 Honest Scraping transparency, and template data contracts.
"""

import pytest
from datetime import date, datetime
from typing import List

from app.models.event import (
    EventItem,
    EventCategory,
    EventConfidence,
    EventStatus,
    EventVenue,
    EventQuery,
    EventSearchResult,
    CategoryEventSummary,
)
from app.services.events.base import BaseEventConnector
from app.services.event_intelligence_service import EventIntelligenceService
from app.services.destination_matching_service import (
    DestinationMatchingService,
    resolve_query_dates,
    compute_event_pricing,
)
from app.services.destination_scoring_service import calculate_destination_rankings
from app.core.config import templates


class MockEventConnector(BaseEventConnector):
    """Konzisztens mock konnektor determinisztikus tesztekhez."""

    def __init__(self, mock_events: List[EventItem]):
        super().__init__(name="mock_connector")
        self.mock_events = mock_events

    async def fetch_events(
        self,
        city: str,
        start_date: date,
        end_date: date,
        is_nye_only: bool = False,
    ) -> List[EventItem]:
        matched = []
        for ev in self.mock_events:
            if ev.city.lower() == city.lower():
                ev_date = ev.start_datetime.date()
                if start_date <= ev_date <= end_date:
                    if not is_nye_only or ev.is_nye_relevant:
                        matched.append(ev)
        return matched


@pytest.fixture
def sample_events():
    v_bcn = EventVenue(name="Poble Espanyol", city="Barcelona")
    v_vlc = EventVenue(name="Marina Beach Club", city="Valencia")

    return [
        EventItem(
            id="ev_bcn_1",
            title="Barcelona NYE Mega Party 2026",
            city="Barcelona",
            venue=v_bcn,
            start_datetime=datetime(2026, 12, 31, 23, 0),
            category=EventCategory.PARTY_NIGHTLIFE,
            price_min=45.0,
            price_max=80.0,
            currency="EUR",
            is_free=False,
            source="eventbrite",
            source_url="https://www.eventbrite.com/e/bcn-nye-mega-party",
            confidence=EventConfidence.SCRAPED_STRUCTURED,
            confidence_score=0.90,
            status=EventStatus.CONFIRMED,
            is_nye_relevant=True,
        ),
        EventItem(
            id="ev_bcn_2",
            title="Gran Gala Flamenco & Tapas",
            city="Barcelona",
            venue=v_bcn,
            start_datetime=datetime(2026, 12, 30, 20, 0),
            category=EventCategory.GASTRONOMY,
            price_min=35.0,
            currency="EUR",
            is_free=False,
            source="local_agenda",
            source_url="https://www.barcelonaturisme.com/agenda/flamenco-tapas",
            confidence=EventConfidence.COMMUNITY_CURATED,
            confidence_score=0.80,
            status=EventStatus.CONFIRMED,
            is_nye_relevant=False,
        ),
        EventItem(
            id="ev_bcn_3",
            title="Symphony of Lights Winter Concert",
            city="Barcelona",
            venue=v_bcn,
            start_datetime=datetime(2027, 1, 1, 18, 0),
            category=EventCategory.MUSIC,
            price_min=None,  # Ár nem megadott -> becslés teszteléséhez
            currency="EUR",
            is_free=False,
            source="ticketmaster",
            source_url="https://www.ticketmaster.es/event/symphony-lights",
            confidence=EventConfidence.VERIFIED_API,
            confidence_score=0.95,
            status=EventStatus.CONFIRMED,
            is_nye_relevant=True,
        ),
        EventItem(
            id="ev_vlc_1",
            title="Valencia Street Art & Food Festival",
            city="Valencia",
            venue=v_vlc,
            start_datetime=datetime(2026, 12, 29, 12, 0),
            category=EventCategory.CULTURE_ARTS,
            price_min=None,
            is_free=False,
            source="local_agenda",
            source_url="https://www.visitvalencia.com/en/agenda/street-art",
            confidence=EventConfidence.COMMUNITY_CURATED,
            confidence_score=0.75,
            status=EventStatus.CONFIRMED,
            is_nye_relevant=False,
        ),
    ]


def test_resolve_query_dates_winter_and_nye():
    """Teszteli a téli/szilveszteri intervallum feloldását és az is_nye detekciót."""
    # 1. Hónap megadása: december (NYE időszak)
    s_date, e_date, is_nye = resolve_query_dates(month=12, year=2026, duration_days=6)
    assert s_date == date(2026, 12, 28)
    assert e_date == date(2027, 1, 3)
    assert is_nye is True

    # 2. Explicit intervallum dec 28 - jan 3
    s_date2, e_date2, is_nye2 = resolve_query_dates(
        out_from="2026-12-28",
        in_to="2027-01-03",
    )
    assert s_date2 == date(2026, 12, 28)
    assert e_date2 == date(2027, 1, 3)
    assert is_nye2 is True

    # 3. Őszi hónap: szeptember (nem NYE)
    s_date3, e_date3, is_nye3 = resolve_query_dates(month=9, year=2026, duration_days=7)
    assert s_date3 == date(2026, 9, 1)
    assert is_nye3 is False


def test_compute_event_pricing_transparency():
    """ADR-004 szigorú transzparencia: valós jegyár vs becslés megkülönböztetése."""
    # 1. Eset: Van ismert ár (45 EUR és 35 EUR) -> min_program_cost = 35 EUR, Valós ár
    ev_real = [
        EventItem(
            id="e1",
            title="Concert",
            city="Barcelona",
            start_datetime=datetime(2026, 12, 31, 20, 0),
            category=EventCategory.MUSIC,
            price_min=45.0,
            source="ticketmaster",
            source_url="https://ticketmaster.com/test",
        ),
        EventItem(
            id="e2",
            title="Show",
            city="Barcelona",
            start_datetime=datetime(2026, 12, 31, 22, 0),
            category=EventCategory.MUSIC,
            price_min=35.0,
            source="ticketmaster",
            source_url="https://ticketmaster.com/test2",
        ),
    ]
    p_real = compute_event_pricing(ev_real)
    assert p_real["min_program_cost_eur"] == 35.0
    assert p_real["is_estimated"] is False
    assert p_real["price_provenance"] == "verified"
    assert p_real["price_badge"] == "Valós ár"

    # 2. Eset: Csak ár nélküli parti esemény -> [Becsült] badge, is_estimated = True
    ev_unpriced = [
        EventItem(
            id="e3",
            title="Club Night",
            city="Valencia",
            start_datetime=datetime(2026, 12, 31, 23, 0),
            category=EventCategory.PARTY_NIGHTLIFE,
            price_min=None,
            source="resident_advisor",
            source_url="https://ra.co/events/123",
        )
    ]
    p_est = compute_event_pricing(ev_unpriced)
    assert p_est["min_program_cost_eur"] == 30.0
    assert p_est["is_estimated"] is True
    assert p_est["price_provenance"] == "estimated"
    assert p_est["price_badge"] == "Becsült"

    # 3. Eset: Nincs esemény
    p_none = compute_event_pricing([])
    assert p_none["min_program_cost_eur"] is None
    assert p_none["is_estimated"] is False
    assert p_none["price_provenance"] == "none"


@pytest.mark.asyncio
async def test_enrich_destinations_with_events_async(sample_events):
    """Teszteli a célállomások aszinkron gazdagítását az EventIntelligenceService-en keresztül."""
    mock_connector = MockEventConnector(sample_events)
    service = EventIntelligenceService(connectors=[mock_connector])

    candidates = [
        {"city": "Barcelona", "name": "Barcelona", "country": "Spain"},
        {"city": "Valencia", "name": "Valencia", "country": "Spain"},
        {"city": "Oslo", "name": "Oslo", "country": "Norway"},  # Nincs esemény
    ]

    start_date = date(2026, 12, 28)
    end_date = date(2027, 1, 3)

    enriched = await DestinationMatchingService.enrich_destinations_with_events_async(
        candidates=candidates,
        start_date=start_date,
        end_date=end_date,
        is_nye_only=False,
        event_service=service,
    )

    # Barcelona: 3 esemény (party, gasztro, zene), valós ár 35 EUR
    bcn = next(c for c in enriched if c["city"] == "Barcelona")
    assert bcn["is_event_enriched"] is True
    assert bcn["event_count"] == 3
    assert len(bcn["top_events"]) == 3
    assert "party_nightlife" in bcn["event_categories"]
    assert "gastronomy" in bcn["event_categories"]
    assert "music" in bcn["event_categories"]
    assert bcn["event_pricing"]["min_program_cost_eur"] == 35.0
    assert bcn["event_pricing"]["is_estimated"] is False
    assert bcn["event_pricing"]["price_badge"] == "Valós ár"

    # Valencia: 1 esemény (ár nélkül) -> Becsült
    vlc = next(c for c in enriched if c["city"] == "Valencia")
    assert vlc["is_event_enriched"] is True
    assert vlc["event_count"] == 1
    assert vlc["event_pricing"]["is_estimated"] is True
    assert vlc["event_pricing"]["price_badge"] == "Becsült"

    # Oslo: 0 esemény
    oslo = next(c for c in enriched if c["city"] == "Oslo")
    assert oslo["is_event_enriched"] is True
    assert oslo["event_count"] == 0
    assert oslo["event_pricing"]["price_provenance"] == "none"


@pytest.mark.asyncio
async def test_evaluate_and_rank_destinations_async_scoring(sample_events):
    """Teszteli, hogy az események jelenléte és diverzitása jutalmazza a 4-pilléres AHP pontszámot."""
    mock_connector = MockEventConnector(sample_events)
    service = EventIntelligenceService(connectors=[mock_connector])

    ranked = await DestinationMatchingService.evaluate_and_rank_destinations_async(
        origin="Budapest",
        out_from="2026-12-28",
        in_to="2027-01-03",
        limit=5,
        event_service=service,
    )

    assert len(ranked) > 0
    top_dest = ranked[0]
    assert "match_score" in top_dest
    assert "s_exp" in top_dest
    assert "is_event_enriched" in top_dest
    assert top_dest["is_event_enriched"] is True


def test_destination_scoring_service_rankings_with_events():
    """Teszteli a calculate_destination_rankings élménypontszám (s_exp) integrációját és kimenetét."""
    raw_candidates = [
        {
            "id": "ES_BCN",
            "name": "Barcelona",
            "city": "Barcelona",
            "country": "Spain",
            "region": "Southern Europe",
            "weather_score_direct": 0.85,
            "event_count": 4,
            "event_categories": ["party_nightlife", "music", "gastronomy"],
            "top_events": [
                {
                    "id": "ev_1",
                    "title": "BCN NYE Festival",
                    "category": "party_nightlife",
                    "price_min": 40.0,
                    "currency": "EUR",
                    "source": "eventbrite",
                    "source_url": "https://eventbrite.com/bcn-nye",
                    "is_nye_relevant": True,
                }
            ],
            "is_event_enriched": True,
            "event_pricing": {
                "min_program_cost_eur": 40.0,
                "is_estimated": False,
                "price_provenance": "verified",
                "price_badge": "Valós ár",
            },
            "raw_metrics": {
                "flight_price_huf": 45000,
                "flight_duration_h": 2.5,
                "daily_cost_eur": 45.0,
                "daily_cost_huf": 18000,
                "total_trip_cost_huf": 210000,
                "safety_index": 72,
                "cost_breakdown": {},
            },
        },
        {
            "id": "NO_OSLO",
            "name": "Oslo",
            "city": "Oslo",
            "country": "Norway",
            "region": "Northern Europe",
            "weather_score_direct": 0.40,
            "event_count": 0,
            "event_categories": [],
            "top_events": [],
            "is_event_enriched": True,
            "event_pricing": {
                "min_program_cost_eur": None,
                "is_estimated": False,
                "price_provenance": "none",
                "price_badge": "N/A",
            },
            "raw_metrics": {
                "flight_price_huf": 65000,
                "flight_duration_h": 3.0,
                "daily_cost_eur": 95.0,
                "daily_cost_huf": 38000,
                "total_trip_cost_huf": 420000,
                "safety_index": 85,
                "cost_breakdown": {},
            },
        },
    ]

    weights = {"total_cost": 25.0, "weather": 25.0, "safety": 25.0, "experience": 25.0}

    results = calculate_destination_rankings(
        candidates_raw=raw_candidates,
        weights=weights,
        target_temp=20.0,
        adults=2,
    )

    assert len(results) == 2
    bcn = next(r for r in results if r["city"] == "Barcelona")
    oslo = next(r for r in results if r["city"] == "Oslo")

    # Barcelona élmény-pontszáma magasabb a gazdag élő programok miatt
    assert bcn["subscores"]["experience"] > oslo["subscores"]["experience"]
    assert bcn["event_count"] == 4
    assert bcn["metrics"]["program_cost_badge"] == "Valós ár"
    assert bcn["metrics"]["program_cost_is_estimated"] is False
    assert any("szilveszteri" in h.lower() for h in bcn["highlights"])


def test_destination_results_template_rendering():
    """Teszteli a destination_results.html sablon szintaxisát és JSON adatátadását."""
    mock_results = [
        {
            "rank": 1,
            "name": "Barcelona",
            "city": "Barcelona",
            "country": "Spanyolország",
            "region": "Dél-Európa",
            "image": "https://example.com/bcn.jpg",
            "score": 88.5,
            "highlights": ["🎆 1 kiemelt szilveszteri program"],
            "explanation": "Kiváló időjárás és gazdag szilveszteri programok",
            "tradeoff": None,
            "subscores": {
                "total_cost": 0.8,
                "flight": 0.8,
                "cost": 0.8,
                "weather": 0.85,
                "safety": 0.75,
                "experience": 0.92,
            },
            "event_count": 3,
            "event_categories": ["party_nightlife", "gastronomy", "music"],
            "is_event_enriched": True,
            "event_pricing": {
                "min_program_cost_eur": 35.0,
                "is_estimated": False,
                "price_provenance": "verified",
                "price_badge": "Valós ár",
            },
            "top_events": [
                {
                    "id": "ev_1",
                    "title": "Razzmatazz NYE 2026",
                    "category": "party_nightlife",
                    "price_min": 35.0,
                    "currency": "EUR",
                    "source": "resident_advisor",
                    "source_url": "https://ra.co/events/12345",
                    "is_nye_relevant": True,
                }
            ],
            "metrics": {
                "temp_formatted": "Nappal: 17°C / Éjjel: 10°C",
                "daily_cost_formatted": "~18 000 Ft / nap",
                "flight_price_formatted": "45 000 Ft",
                "flight_price_per_person_formatted": "45 000 Ft / fő",
                "safety_formatted": "72/100 (Numbeo)",
                "adults": 2,
            },
        }
    ]

    from starlette.requests import Request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/destination-results",
        "headers": [],
    }
    req = Request(scope)

    rendered = templates.TemplateResponse(
        "destination/destination_results.html",
        {
            "request": req,
            "results": mock_results,
            "constraints": {
                "origin": "Budapest",
                "month": "12",
                "duration": 6,
                "adults": 2,
                "out_from": "2026-12-28",
                "in_to": "2027-01-03",
            },
        },
    )

    body = rendered.body.decode("utf-8")
    assert "Legjobb úticélok számodra" in body
    assert "results-data" in body
    assert "Razzmatazz NYE 2026" in body
    assert "https://ra.co/events/12345" in body
    assert "[Valós ár]" in body or "Valós ár" in body
