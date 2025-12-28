from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ScraperInterface(ABC):
    """
    Abstract interface for social media scraping.
    """
    
    @abstractmethod
    def get_profile_info(self, username: str) -> Dict[str, Any]:
        """
        Fetch profile metadata.
        """
        pass

    @abstractmethod
    def get_posts(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent posts from a profile.
        """
        pass
