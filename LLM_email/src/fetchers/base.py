from abc import ABC, abstractmethod
from typing import List
from src.models import AccountConfig, RawEmail


class BaseEmailFetcher(ABC):
    """Absztrakt alaposztály az email fiókok adatgyűjtő adaptereihez."""

    def __init__(self, account: AccountConfig):
        self.account = account

    @abstractmethod
    def test_connection(self) -> bool:
        """Teszteli a fiókhoz való kapcsolódást."""
        pass

    @abstractmethod
    def fetch_recent_emails(self, hours: int = 24) -> List[RawEmail]:
        """Lekéri az elmúlt X órában érkezett emaileket."""
        pass
