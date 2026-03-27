import tls_client
from bs4 import BeautifulSoup
import random
import time
import pandas as pd
from typing import List, Dict, Any

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

CLIENT_IDENTIFIERS = ["chrome_120", "firefox_120", "safari_ios_16_0"]

class EbayScraper:
    def __init__(self):
        self.session = tls_client.Session(client_identifier=random.choice(CLIENT_IDENTIFIERS))
        # Remove cookies for now to see if base session + headers work better
        
    def _get_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=1.0",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def fetch_sold_items(self, query: str, pages: int = 1) -> List[Dict[str, Any]]:
        results = []
        for page in range(1, pages + 1):
            # Added _ipg=200 and _stpos=10001 (US Zip) to nudge towards US layout
            url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1&_pgn={page}&_ipg=60&_osacat=0&_from=R40&rt=nc"
            try:
                time.sleep(random.uniform(1.5, 3.0))
                headers = self._get_headers()
                resp = self.session.get(url, headers=headers)
                
                if resp.status_code != 200:
                    print(f"Error fetching {url}: {resp.status_code}")
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Check for two common layouts
                items = soup.select('.s-item__wrapper')
                if not items:
                    items = soup.select('.s-card') # Browser subagent found this
                
                if not items:
                    # Log for debugging if still empty
                    if page == 1:
                        print(f"No items found for: {query} (Layout might have changed)")
                    continue
                
                for item in items:
                    # Multi-selector logic for title/price
                    title_el = item.select_one('.s-item__title, .s-card__title')
                    price_el = item.select_one('.s-item__price, .s-card__price')
                    date_el = item.select_one('.s-item__title--tagblock .POSITIVE, .s-card__sold-date')
                    
                    if not title_el or not price_el:
                        continue
                        
                    title = title_el.get_text(strip=True)
                    # Remove the hidden "New window" text added by eBay for screen readers
                    for suffix in ["Új ablakban vagy lapon nyílik meg", "Opens in a new window or tab"]:
                        title = title.replace(suffix, "").strip()
                        
                    if "Shop on eBay" in title or "Hirdetés" in title: # Handle HU translation for "Ad"
                        continue
                        
                    price_raw = price_el.get_text(strip=True)
                    date_raw = date_el.get_text(strip=True) if date_el else ""
                    
                    # Basic price parsing
                    price_clean = price_raw.replace('\xa0', ' ').replace(',', '.')
                    # Extract numeric value and currency (naive approach for now)
                    # e.g. "61 864.93 HUF" -> 61864.93, HUF
                    
                    results.append({
                        'title': title,
                        'price_raw': price_raw,
                        'price_clean': price_clean,
                        'date_raw': date_raw.replace('Sold ', '').replace('Eladva ', ''), # Handle HU
                        'query': query
                    })
            except Exception as e:
                print(f"Exception during eBay scrape for {query}: {e}")
                
        return results

if __name__ == "__main__":
    scraper = EbayScraper()
    items = scraper.fetch_sold_items("Erling Haaland 2019 Topps Chrome", pages=1)
    print(f"Found {len(items)} items for Haaland")
    for item in items[:3]:
        print(item)
