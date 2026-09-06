from datetime import datetime
from src.models import AccountConfig, EmailAnalysis, RawEmail, ProcessedEmail


def test_account_config_defaults():
    acc = AccountConfig(
        id="acc_1",
        name="Test Account",
        username="user@example.com",
        password="secretpassword",
    )
    assert acc.category == "egyéb"
    assert acc.imap_port == 993
    assert acc.use_ssl is True
    assert acc.enabled is True


def test_raw_email_model():
    raw = RawEmail(
        message_id="msg-12345",
        account_id="acc_1",
        account_name="Test Account",
        default_category="munka",
        sender="boss@example.com",
        recipient="me@example.com",
        subject="Heti megbeszélés",
        date=datetime.now(),
        body_text="Kérlek készítsd el a riportot péntek 12:00-ig.",
    )
    assert raw.message_id == "msg-12345"
    assert raw.subject == "Heti megbeszélés"


def test_processed_email_model():
    raw = RawEmail(
        message_id="msg-1",
        account_id="acc_1",
        account_name="Test",
        sender="a@b.com",
        subject="Test",
        date=datetime.now(),
        body_text="Test body",
    )
    analysis = EmailAnalysis(
        category="munka",
        urgency="magas",
        importance="kiemelt",
        summary="Fontos munkahelyi feladat.",
        action_items=["Riport készítése"],
        deadlines=["Péntek 12:00"],
    )
    processed = ProcessedEmail(raw=raw, analysis=analysis)
    assert processed.analysis.urgency == "magas"
    assert len(processed.analysis.action_items) == 1
