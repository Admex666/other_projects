import tls_client
from bs4 import BeautifulSoup
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def test_ebay_rss(query):
    session = tls_client.Session(client_identifier="chrome_120")
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    # RSS URL trick
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1&_rss=1"
    print(f"Fetching RSS: {url}")
    resp = session.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'xml') # RSS is XML
    
    items = soup.find_all('item')
    print(f"Found {len(items)} RSS items")
    
    for item in items[:5]:
        title = item.find('title').get_text(strip=True)
        link = item.find('link').get_text(strip=True)
        print(f" - {title}")
        # print(f"   Link: {link}")

if __name__ == "__main__":
    test_ebay_rss("Erling Haaland 2019 Topps Chrome")
