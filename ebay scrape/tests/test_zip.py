import tls_client
from bs4 import BeautifulSoup
import random

def test_zip_code_force(query):
    session = tls_client.Session(client_identifier="chrome_120")
    
    # Precise headers and cookies from the browser subagent's successful session
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.ebay.com/",
        "DNT": "1",
        "UPGRADE-INSECURE-REQUESTS": "1",
        "SEC-FETCH-DEST": "document",
        "SEC-FETCH-MODE": "navigate",
        "SEC-FETCH-SITE": "same-origin",
        "SEC-FETCH-USER": "?1"
    }
    
    # Cookies to force US/English
    session.cookies.set("dp1", "bl/HUen-US", domain=".ebay.com")
    session.cookies.set("nonsession", "siteid=0", domain=".ebay.com")
    session.cookies.set("ebay", "cos=0", domain=".ebay.com")
    
    # URL with US Zip code (10001 = New York)
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1&_stpos=10001&_localstpos=10001&_gbr=1"
    
    print(f"Fetching {url}...")
    resp = session.get(url, headers=headers)
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    html_lang = soup.find('html').get('lang') if soup.find('html') else 'unknown'
    print(f"HTML Lang: {html_lang}")
    
    # Check for "Search" button text
    search_btn = soup.select_one('#gh-btn')
    if search_btn:
        print(f"Search Button Text: {search_btn.get('value') or search_btn.get_text()}")

    items = soup.select('.s-item__wrapper, .s-card')
    print(f"Found {len(items)} items")
    for item in items[:5]:
        title_el = item.select_one('.s-item__title, .s-card__title')
        if title_el:
            title = title_el.get_text(strip=True).replace("Opens in a new window or tab", "").strip()
            print(f" - {title}")

if __name__ == "__main__":
    test_zip_code_force("Erling Haaland 2019 Topps Chrome")
