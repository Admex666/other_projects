from datetime import datetime
from unittest.mock import MagicMock
from src.analyzer.gemini_analyzer import GeminiEmailAnalyzer
from src.models import EmailAnalysis, ProcessedEmail, RawEmail


def test_gemini_analyzer_parsing():
    analyzer = GeminiEmailAnalyzer(api_key="fake_key")
    analyzer.client = MagicMock()

    mock_resp = MagicMock()
    mock_resp.text = """{
        "category": "munka",
        "urgency": "magas",
        "importance": "kiemelt",
        "needs_reply": true,
        "is_interesting_news": false,
        "priority_score": 9,
        "summary": "Projekt státusz megbeszélés sürgős feladatokkal.",
        "action_items": ["Adatbázis migrálása", "Prezentáció ellenőrzése"],
        "deadlines": ["Holnap 10:00"]
    }"""
    mock_resp.usage_metadata = MagicMock(total_token_count=180)
    analyzer.client.models.generate_content.return_value = mock_resp

    raw = RawEmail(
        message_id="msg-1",
        account_id="work",
        account_name="Munka",
        default_category="munka",
        sender="pm@company.com",
        subject="Sprint zárás",
        date=datetime.now(),
        body_text="Kérlek válaszolj és fejezd be a migrációt holnap 10:00-ig.",
    )

    analysis = analyzer.analyze_email(raw)
    assert analysis.category == "munka"
    assert analysis.urgency == "magas"
    assert analysis.needs_reply is True
    assert analysis.priority_score == 9
    assert len(analysis.action_items) == 2
    assert "Holnap 10:00" in analysis.deadlines


def test_gemini_daily_digest_prioritization():
    analyzer = GeminiEmailAnalyzer(api_key="fake_key")

    mail_reply = ProcessedEmail(
        raw=RawEmail(
            message_id="msg-reply",
            account_id="work",
            account_name="Munka",
            sender="boss@company.com",
            subject="Kérdés az ajánlatról",
            date=datetime.now(),
            body_text="Légyszi küldd át!",
        ),
        analysis=EmailAnalysis(
            category="munka",
            urgency="magas",
            needs_reply=True,
            priority_score=9,
            summary="Ajánlat bekérése a főnöktől.",
            action_items=["Elküldeni az ajánlatot"],
            deadlines=["Ma 17:00"],
        ),
    )

    mail_news = ProcessedEmail(
        raw=RawEmail(
            message_id="msg-news",
            account_id="personal",
            account_name="Személyes",
            sender="newsletter@tech.com",
            subject="Heti AI hírlevél",
            date=datetime.now(),
            body_text="Új modellek jelentek meg.",
        ),
        analysis=EmailAnalysis(
            category="hírlevél/cikk",
            urgency="alacsony",
            needs_reply=False,
            is_interesting_news=True,
            priority_score=6,
            summary="Új nyílt forráskódú LLM-ek összefoglalója.",
        ),
    )

    digest = analyzer.generate_daily_digest([mail_reply, mail_news])

    assert "VÁLASZT IGÉNYLŐ LEVELEK" in digest
    assert "Kérdés az ajánlatról" in digest
    assert "RELEVÁNS HÍREK & CIKKEK" in digest
    assert "Heti AI hírlevél" in digest
    # Biztosítjuk, hogy a válaszolós szekció előbb jelenik meg, mint a hírek
    reply_pos = digest.find("VÁLASZT IGÉNYLŐ LEVELEK")
    news_pos = digest.find("RELEVÁNS HÍREK")
    assert reply_pos < news_pos
