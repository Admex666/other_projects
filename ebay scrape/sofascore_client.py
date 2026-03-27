import pandas as pd
import json
import time
import random
from typing import Dict, Any, Optional, List
import tls_client

# Constants for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

CLIENT_IDENTIFIERS = ["chrome_120", "chrome_119", "firefox_120"]

class SofaScoreClient:
    def __init__(self):
        self.session_pool = []
        self.last_request_time = 0
        self.request_count = 0
        
    def _get_session(self):
        if not self.session_pool or random.random() < 0.2:
            client_id = random.choice(CLIENT_IDENTIFIERS)
            sess = tls_client.Session(client_identifier=client_id)
            self.session_pool.append(sess)
            if len(self.session_pool) > 5:
                self.session_pool.pop(0)
        return random.choice(self.session_pool)

    def _rate_limit(self):
        current_time = time.time()
        delay = 1.0 + random.uniform(0.5, 1.5)
        if current_time - self.last_request_time < delay:
            time.sleep(delay - (current_time - self.last_request_time))
        self.last_request_time = time.time()

    def _get_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "DNT": "1",
        }

    def scrape_api(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        self._rate_limit()
        for attempt in range(max_retries):
            try:
                sess = self._get_session()
                resp = sess.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    time.sleep(2 ** attempt + 1)
                    self.session_pool = []
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                time.sleep(1)
        return {}

    def get_top_young_players(self, tournament_id: int, season_id: int, max_age: int = 23, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches top rated players for a tournament/season and filters by age."""
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/statistics?type=overall&order=-rating&offset=0&limit=100"
        data = self.scrape_api(url)
        
        young_players = []
        if 'results' in data:
            for entry in data['results']:
                player = entry.get('player')
                if not player: continue
                
                # Fetch full info to get age if not present
                info = self.get_player_info(player['id'])
                age = info.get('age')
                
                if age and age <= max_age:
                    stats = entry.get('statistics', {})
                    young_players.append({
                        'id': player['id'],
                        'name': player['name'],
                        'age': age,
                        'rating': stats.get('rating', 0),
                        'team': entry.get('team', {}).get('name', 'Unknown'),
                        'marketValue': info.get('marketValue', 0)
                    })
                
                if len(young_players) >= limit:
                    break
        return young_players

    def get_player_info(self, player_id: int) -> Dict[str, Any]:
        """Fetches detailed player profile including age and market value."""
        url = f"https://api.sofascore.com/api/v1/player/{player_id}"
        data = self.scrape_api(url)
        if 'player' in data:
            p = data['player']
            return {
                'id': p['id'],
                'age': 2024 - time.gmtime(p.get('dateOfBirthTimestamp', 0)).tm_year if p.get('dateOfBirthTimestamp') else None,
                'position': p.get('position', ''),
                'marketValue': p.get('proposedMarketValue', 0),
                'nationality': p.get('country', {}).get('name', '')
            }
        return {}

    def get_player_season_stats(self, player_id: int, tournament_id: int, season_id: int) -> Dict[str, Any]:
        """Fetches core stats for the prediction model (G/A per 90, etc)."""
        url = f"https://api.sofascore.com/api/v1/player/{player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
        data = self.scrape_api(url)
        if 'statistics' in data:
            s = data['statistics']
            appearances = s.get('appearances', 0)
            minutes = s.get('minutesPlayed', 0)
            if minutes == 0: return {}
            
            return {
                'rating': s.get('rating', 0),
                'goals_per_90': (s.get('goals', 0) / minutes) * 90,
                'assists_per_90': (s.get('assists', 0) / minutes) * 90,
                'xg_per_90': (s.get('expectedGoals', 0) / minutes) * 90,
                'minutes_played': minutes,
                'matches': appearances
            }
        return {}

if __name__ == "__main__":
    client = SofaScoreClient()
    # Test with Premier League (17, 52186 = 23/24)
    print("Testing SofaScore Client...")
    players = client.get_top_young_players(17, 52186, limit=5)
    print(f"Found {len(players)} players.")
    for p in players:
        info = client.get_player_info(p['id'])
        print(f"Player: {p['name']} | Rating: {p['rating']} | Age: {info.get('age')} | MV: {info.get('marketValue')}")
