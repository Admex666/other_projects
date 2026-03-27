import tls_client
from bs4 import BeautifulSoup
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def test_ebay_us_force(query):
    session = tls_client.Session(client_identifier="chrome_120")
    
    # Headers without explicit encoding to avoid the gzip error
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    
    # Set the cookie directly on the session
    # siteid=0 is US
    session.cookies.set("nonsession", "siteid=0", domain=".ebay.com")
    session.cookies.set("ebay", "cos=0", domain=".ebay.com")
    
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"
    print(f"Fetching {url}...")
    resp = session.get(url, headers=headers)
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    html_tag = soup.find('html')
    lang = html_tag.get('lang') if html_tag else 'unknown'
    print(f"Detected Page Language: {lang}")
    
    items = soup.select('.s-item__wrapper, .s-card')
    print(f"Found {len(items)} items")
    
    for item in items[:3]:
        title_el = item.select_one('.s-item__title, .s-card__title')
        if title_el:
            title = title_el.get_text(strip=True)
            # Clean title suffix
            title = title.replace("Opens in a new window or tab", "").replace("Új ablakban vagy lapon nyílik meg", "").strip()
            print(f" - {title}")

if __name__ == "__main__":
    test_ebay_us_force("Erling Haaland 2019 Topps Chrome")
