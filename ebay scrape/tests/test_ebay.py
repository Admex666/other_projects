import tls_client
from bs4 import BeautifulSoup
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def test_ebay(query):
    session = tls_client.Session(client_identifier="chrome_120")
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.ebay.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
    }
    
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}"
    print(f"Fetching {url}...")
    resp = session.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    items = soup.select('.s-item__wrapper')
    print(f"Found {len(items)} items")
    
    if len(items) == 0:
        with open("test_ebay_fail.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Saved failure HTML to test_ebay_fail.html")
    else:
        for item in items[:3]:
            title = item.select_one('.s-item__title')
            if title:
                print(f" - {title.get_text(strip=True)}")

if __name__ == "__main__":
    test_ebay("iPhone")
