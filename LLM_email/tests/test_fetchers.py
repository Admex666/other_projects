from unittest.mock import patch, MagicMock
from src.models import AccountConfig
from src.fetchers.graph_fetcher import GraphEmailFetcher


def test_graph_fetcher_initialization():
    acc = AccountConfig(
        id="test_graph",
        name="Test Graph",
        provider="graph",
        username="user@domain.com",
    )
    fetcher = GraphEmailFetcher(acc)
    assert fetcher.client_id is not None
    assert fetcher.authority == "https://login.microsoftonline.com/organizations"


def test_graph_fetcher_fetch_recent_mocked():
    acc = AccountConfig(
        id="test_graph",
        name="Test Graph",
        provider="graph",
        username="user@domain.com",
    )
    fetcher = GraphEmailFetcher(acc)

    with patch.object(fetcher, "acquire_token", return_value="mocked_token"), \
         patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "value": [
                    {
                        "id": "graph-1",
                        "internetMessageId": "msg-graph-100",
                        "subject": "Microsoft 365 Értesítés",
                        "from": {"emailAddress": {"name": "Admin", "address": "admin@domain.com"}},
                        "toRecipients": [{"emailAddress": {"address": "user@domain.com"}}],
                        "receivedDateTime": "2026-09-06T12:00:00Z",
                        "body": {"contentType": "text", "content": "Rendszerfrissítés lesz."},
                    }
                ]
            },
        )

        emails = fetcher.fetch_recent_emails(hours=24)
        assert len(emails) == 1
        assert emails[0].subject == "Microsoft 365 Értesítés"
        assert emails[0].message_id == "msg-graph-100"
