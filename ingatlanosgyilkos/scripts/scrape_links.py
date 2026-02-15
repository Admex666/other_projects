import argparse
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
from typing import List
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_headers():
    """
    Returns headers that mimic Google Bot to access SSR content.
    """
    return {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Referer": "https://www.google.com/",
        "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def scrape_page(url: str) -> List[str]:
    """
    Scrapes listing links from a single search results page using requests and BeautifulSoup.
    """
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Find all links starting with /ingatlan/
        # Zenga structure: <a href="/ingatlan/elado-...">
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filter for property links (usually start with /ingatlan/ and have some ID)
            # Avoid general links like /ingatlan-hirdetes-feladas
            if href.startswith('/ingatlan/') and href.count('-') > 2:
                full_url = f"https://www.zenga.hu{href}"
                if full_url not in links:
                    links.append(full_url)
        
        return links
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return []

def scrape_links(listing_type: str, num_pages: int, start_page: int = 1):
    """
    Scrape links for a given listing type.
    """
    base_url = f"https://www.zenga.hu/budapest+{listing_type}+lakas"
    all_links = []
    
    logger.info(f"🚀 Starting scrape for {listing_type} listings")
    
    for page in range(start_page, start_page + num_pages):
        url = f"{base_url}?page={page}"
        logger.info(f"📄 Page {page}/{start_page + num_pages - 1}")
        
        page_links = scrape_page(url)
        
        if not page_links:
            logger.warning(f"⚠️ No links found on page {page}. Stopping.")
            break
            
        logger.info(f"   Date: found {len(page_links)} links")
        all_links.extend(page_links)
        
        # Be polite
        time.sleep(2)
        
    return pd.DataFrame(all_links, columns=['url'])

def main():
    parser = argparse.ArgumentParser(description='Scrape Zenga real estate links.')
    parser.add_argument('--type', type=str, choices=['elado', 'kiado'], required=True, help='Type of listing (sale/rent)')
    parser.add_argument('--num-pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--start-page', type=int, default=1, help='Starting page number')
    parser.add_argument('--output', type=str, default='data/raw/zenga_links.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    df = scrape_links(args.type, args.num_pages, args.start_page)
    
    if not df.empty:
        # Remove duplicates
        df = df.drop_duplicates()
        df.to_csv(args.output, index=False)
        logger.info(f"✅ Successfully saved {len(df)} links to {args.output}")
    else:
        logger.error("❌ No links found!")

if __name__ == "__main__":
    main()
