import random
import datetime
from typing import List, Dict, Any
from .scraper_interface import ScraperInterface

class MockInstagramScraper(ScraperInterface):
    """
    Mock implementation of Instagram scraping for testing and development.
    """
    
    def get_profile_info(self, username: str) -> Dict[str, Any]:
        return {
            "username": username,
            "follower_count": random.randint(1000, 1000000),
            "biography": f"Official {username} account. Digital Creator.",
            "post_count": random.randint(50, 500)
        }

    def get_posts(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        posts = []
        base_date = datetime.datetime.now()
        
        for i in range(count):
            post_date = base_date - datetime.timedelta(days=i)
            posts.append({
                "post_id": f"post_{username}_{i}",
                "timestamp": post_date.isoformat(),
                "caption": f"This is a sample post caption for {username}. #awesome #socialmedia {i}",
                "likes": random.randint(100, 50000),
                "comments": random.randint(5, 500),
                "is_reel": random.choice([True, False]),
                "media_type": "IMAGE" if i % 2 == 0 else "CAROUSEL",
                "media_url": f"https://picsum.photos/seed/{username}_{i}/1080/1080"
            })
        return posts
