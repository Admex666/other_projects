import tls_client
from bs4 import BeautifulSoup
import random

def test_minimal_headers(query):
    session = tls_client.Session(client_identifier="chrome_120")
    
    # Minimalist headers, NO 'hu' trace
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Try adding a generic US preference cookie
    session.cookies.set("dp1", "bl/en-US", domain=".ebay.com")
    session.cookies.set("reg_cur", "USD", domain=".ebay.com")
    
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"
    print(f"Fetching {url} with minimal headers...")
    resp = session.get(url, headers=headers)
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    html_lang = soup.find('html').get('lang') if soup.find('html') else 'unknown'
    print(f"HTML Lang: {html_lang}")
    
    items = soup.select('.s-item__wrapper, .s-card')
    for item in items[:5]:
        title_el = item.select_one('.s-item__title, .s-card__title')
        if title_el:
            title = title_el.get_text(strip=True).replace("Opens in a new window or tab", "").strip()
            print(f" - {title}")

if __name__ == "__main__":
    test_minimal_headers("Erling Haaland 2019 Topps Chrome")
