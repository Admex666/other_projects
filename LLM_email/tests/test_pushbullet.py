from unittest.mock import patch, MagicMock
from src.notifier.pushbullet import PushbulletNotifier


def test_pushbullet_notifier():
    notifier = PushbulletNotifier(access_token="test_token")

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        success = notifier.send_push(title="Cím", body="Üzenet törzs")
        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["title"] == "Cím"
        assert kwargs["json"]["body"] == "Üzenet törzs"
        assert kwargs["headers"]["Access-Token"] == "test_token"
