from datetime import datetime
from pathlib import Path
from src.models import EmailAnalysis, ProcessedEmail, RawEmail
from src.storage.db import EmailDatabase


def test_sqlite_storage(tmp_path: Path):
    db_file = tmp_path / "test_emails.db"
    db = EmailDatabase(db_file)

    assert db.get_recent_count() == 0
    assert not db.is_processed("msg-1")

    raw = RawEmail(
        message_id="msg-1",
        account_id="acc_test",
        account_name="Test Account",
        default_category="személyes",
        sender="friend@example.com",
        subject="Találkozó",
        date=datetime.now(),
        body_text="Szia, találkozunk ma?",
    )
    analysis = EmailAnalysis(
        category="személyes",
        urgency="alacsony",
        importance="normál",
        summary="Baráti találkozó egyeztetése.",
        action_items=["Válaszolni"],
        deadlines=[],
    )
    processed = ProcessedEmail(raw=raw, analysis=analysis)

    db.save_processed_email(processed)

    assert db.is_processed("msg-1")
    assert not db.is_processed("msg-2")
    assert db.get_recent_count() == 1

    # Idempotencia és szűrés tesztelése
    unprocessed = db.filter_unprocessed_ids(["msg-1", "msg-2", "msg-3"])
    assert unprocessed == {"msg-2", "msg-3"}
