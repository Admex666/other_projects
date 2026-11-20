import pytest
from datetime import datetime, date
from app.models.event import (
    EventItem,
    EventCategory,
    EventConfidence,
    EventStatus,
    EventVenue,
    EventQuery,
    EventSearchResult,
)
from app.services.events.base import BaseEventConnector
from app.services.event_intelligence_service import EventIntelligenceService


def test_event_item_validation():
    """Teszteli az EventItem validációs szabályait és Pydantic megszorításait."""
    venue = EventVenue(name="Razzmatazz", city="Barcelona")
    ev = EventItem(
        id="ev_test_1",
        title="NYE Countdown Party 2026",
        city="Barcelona",
        venue=venue,
        start_datetime=datetime(2026, 12, 31, 23, 0),
        category=EventCategory.PARTY_NIGHTLIFE,
        source="eventbrite",
        source_url="https://www.eventbrite.com/e/test-party-12345",
        confidence=EventConfidence.SCRAPED_STRUCTURED,
        confidence_score=0.85,
        status=EventStatus.CONFIRMED,
        is_nye_relevant=True
    )
    assert ev.title == "NYE Countdown Party 2026"
    assert ev.is_nye_relevant is True
    assert ev.source_url.startswith("https://")


def test_event_item_invalid_url():
    """ADR-004: Fiktív vagy hiányzó URL esetén a modell érvénytelen."""
    venue = EventVenue(name="Test Club", city="Valencia")
    with pytest.raises(ValueError):
        EventItem(
            id="ev_invalid_url",
            title="Fake Event",
            city="Valencia",
            venue=venue,
            start_datetime=datetime(2026, 12, 31, 22, 0),
            source="manual",
            source_url="invalid_url_without_http",
        )


def test_category_classification():
    """Teszteli a regex-alapú kategóriabesorolást."""
    assert BaseEventConnector.classify_category("Carl Cox NYE Rave DJ Set") == EventCategory.PARTY_NIGHTLIFE
    assert BaseEventConnector.classify_category("Symphonic Orchestra Winter Concert") == EventCategory.MUSIC
    assert BaseEventConnector.classify_category("New Year's Eve Gala Tapas & Wine Tasting") == EventCategory.GASTRONOMY
    assert BaseEventConnector.classify_category("Modern Art Museum Guided Tour & Exhibition") == EventCategory.CULTURE_ARTS
    assert BaseEventConnector.classify_category("San Silvestre 10k City Run") == EventCategory.SPORTS_WELLNESS


def test_nye_relevance_detection():
    """Teszteli a szilveszteri relevanciát dátum és kulcsszavak alapján."""
    # Dec 31 automatikusan NYE
    dt_nye = datetime(2026, 12, 31, 23, 0)
    assert BaseEventConnector.detect_nye_relevance("Regular Club Night", None, dt_nye) is True

    # Jan 1 automatikusan NYE
    dt_new_year = datetime(2027, 1, 1, 14, 0)
    assert BaseEventConnector.detect_nye_relevance("After Party", None, dt_new_year) is True

    # Dec 29 kulcsszóval
    dt_early = datetime(2026, 12, 29, 21, 0)
    assert BaseEventConnector.detect_nye_relevance("MOTHERSHIP NYE Warm Up", None, dt_early) is True

    # Dec 29 kulcsszó nélkül NEM NYE
    assert BaseEventConnector.detect_nye_relevance("Local Jazz Trio", None, dt_early) is False


def test_honest_date_range_validation():
    """ADR-004: Kizárja az elavult vagy időintervallumon kívül eső rendezvényeket."""
    start_d = date(2026, 12, 28)
    end_d = date(2027, 1, 3)

    in_range_dt = datetime(2026, 12, 31, 22, 0)
    out_range_past = datetime(2026, 11, 20, 20, 0)
    out_range_future = datetime(2027, 4, 15, 18, 0)

    assert BaseEventConnector.is_within_range(in_range_dt, start_d, end_d) is True
    assert BaseEventConnector.is_within_range(out_range_past, start_d, end_d) is False
    assert BaseEventConnector.is_within_range(out_range_future, start_d, end_d) is False


def test_deduplication():
    """Teszteli az azonos események összevonását és a magasabb confidence score prioritását."""
    service = EventIntelligenceService(connectors=[])
    venue = EventVenue(name="Club Spook", city="Valencia")

    ev1 = EventItem(
        id="ev_low",
        title="Spook NYE Techno Night",
        city="Valencia",
        venue=venue,
        start_datetime=datetime(2026, 12, 31, 23, 0),
        source="local_agenda",
        source_url="https://agenda.valencia.es/spook",
        confidence=EventConfidence.COMMUNITY_CURATED,
        confidence_score=0.70,
        price_min=None
    )

    ev2 = EventItem(
        id="ev_high",
        title="Spook NYE Techno Night",
        city="Valencia",
        venue=venue,
        start_datetime=datetime(2026, 12, 31, 23, 0),
        source="resident_advisor",
        source_url="https://ra.co/events/9999",
        confidence=EventConfidence.SCRAPED_STRUCTURED,
        confidence_score=0.90,
        price_min=25.0,
        currency="EUR"
    )

    deduped = service._deduplicate_events([ev1, ev2])
    assert len(deduped) == 1
    assert deduped[0].confidence_score == 0.90
    assert deduped[0].source == "resident_advisor"
    assert deduped[0].price_min == 25.0


@pytest.mark.asyncio
async def test_search_events_service_flow():
    """End-to-end integrációs teszt mock adatokkal a szolgáltatási folyamat ellenőrzésére."""
    class DummyConnector(BaseEventConnector):
        def __init__(self):
            super().__init__(name="dummy_verified")

        async def fetch_events(self, city, start_date, end_date, is_nye_only=False):
            return [
                EventItem(
                    id="ev_dummy_1",
                    title="Malaga Symphony New Year Gala Concert",
                    city=city,
                    venue=EventVenue(name="Teatro Cervantes", city=city),
                    start_datetime=datetime(2027, 1, 1, 19, 0),
                    category=EventCategory.MUSIC,
                    source="dummy_verified",
                    source_url="https://teatrocervantes.com/gala2027",
                    confidence=EventConfidence.VERIFIED_API,
                    confidence_score=0.95,
                    is_nye_relevant=True
                )
            ]

    service = EventIntelligenceService(connectors=[DummyConnector()])
    query = EventQuery(
        city="Malaga",
        start_date=date(2026, 12, 28),
        end_date=date(2027, 1, 3),
        is_nye_only=True
    )

    result = await service.search_events(query)
    assert result.city == "Malaga"
    assert result.total_events == 1
    assert result.honest_validation_passed is True
    assert "music" in result.categories
    assert result.categories["music"].count == 1
    assert result.categories["music"].events[0].title == "Malaga Symphony New Year Gala Concert"
