from datetime import datetime
from unittest.mock import MagicMock
from src.analyzer.groq_analyzer import GroqEmailAnalyzer
from src.models import EmailAnalysis, ProcessedEmail, RawEmail


def test_groq_analyzer_parsing():
    analyzer = GroqEmailAnalyzer(api_key="fake_key")
    analyzer.client = MagicMock()

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
                    "category": "munka",
                    "urgency": "magas",
                    "importance": "kiemelt",
                    "summary": "Projekt státusz megbeszélés sürgős feladatokkal.",
                    "action_items": ["Adatbázis migrálása", "Prezentáció ellenőrzése"],
                    "deadlines": ["Holnap 10:00"]
                }"""
            )
        )
    ]
    mock_completion.usage = MagicMock(total_tokens=150)

    mock_raw = MagicMock()
    mock_raw.headers = {
        "x-ratelimit-limit-requests": "1000",
        "x-ratelimit-remaining-requests": "990",
    }
    mock_raw.parse.return_value = mock_completion
    analyzer.client.chat.completions.with_raw_response.create.return_value = mock_raw

    raw = RawEmail(
        message_id="msg-1",
        account_id="work",
        account_name="Munka",
        default_category="munka",
        sender="pm@company.com",
        subject="Sprint zárás",
        date=datetime.now(),
        body_text="Kérlek fejezzétek be a migrációt holnap 10:00-ig.",
    )

    analysis = analyzer.analyze_email(raw)
    assert analysis.category == "munka"
    assert analysis.urgency == "magas"
    assert len(analysis.action_items) == 2
    assert "Holnap 10:00" in analysis.deadlines


def test_generate_daily_digest():
    analyzer = GroqEmailAnalyzer(api_key="fake_key")
    raw = RawEmail(
        message_id="msg-1",
        account_id="uni",
        account_name="Egyetem",
        default_category="egyetem",
        sender="tanar@uni.hu",
        subject="Vizsga feliratkozás",
        date=datetime.now(),
        body_text="A vizsga feliratkozási határidő péntek éjfél.",
    )
    analysis = EmailAnalysis(
        category="egyetem",
        urgency="kritikus",
        importance="kiemelt",
        summary="Vizsga feliratkozási határidő.",
        action_items=["Feliratkozni a Neptunban"],
        deadlines=["Péntek éjfél"],
    )
    processed = [ProcessedEmail(raw=raw, analysis=analysis)]

    digest = analyzer.generate_daily_digest(processed)
    assert "Napi Email Összesítő" in digest
    assert "SÜRGŐS" in digest
    assert "Vizsga feliratkozás" in digest
    assert "Péntek éjfél" in digest
