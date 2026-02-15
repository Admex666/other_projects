import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Referer": "https://www.google.com/",
        "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def extract_price(soup):
    """Extract property price from various formats (Millions, Thousands, Raw)."""
    
    # Strategy 1: Check H1 first (Most reliable for Zenga)
    if soup.h1:
        h1_text = soup.h1.get_text(strip=True)
        
        # 1. Matches "380 millió Ft" or "380,5 millió Ft"
        match_million = re.search(r'(\d+[\.,]?\d*)\s*millió\s*Ft', h1_text, re.IGNORECASE)
        if match_million:
            num_str = match_million.group(1).replace(',', '.')
            return int(float(num_str) * 1_000_000)
            
        # 2. Matches "250 ezer Ft"
        match_thousand = re.search(r'(\d+)\s*ezer\s*Ft', h1_text, re.IGNORECASE)
        if match_thousand:
             return int(match_thousand.group(1)) * 1_000

        # 3. Matches raw "250 000 Ft" or "250.000 Ft" or "250 000 Ft/hó"
        # Remove common separators to simplify matching
        clean_text = h1_text.replace('\xa0', '').replace('.', '').replace(' ', '')
        match_raw = re.search(r'(\d+)Ft', clean_text, re.IGNORECASE)
        if match_raw:
             return int(match_raw.group(1))

    # Strategy 2: Look for specific price elements in body
    # Class: fc-text-primary fs-24 fw-700
    price_candidates = soup.find_all('div', class_=lambda c: c and 'fc-text-primary' in c)
    for div in price_candidates:
        text = div.get_text(strip=True)
        if "Ft" in text:
            digits = re.sub(r'[^\d]', '', text)
            if digits:
                return int(digits)

    # Strategy 3: Look for labels (Irányár, Bérleti díj)
    price_label = soup.find(string=re.compile(r"Irányár|Vételár|Ár:|Bérleti díj|Havi díj", re.IGNORECASE))
    if price_label:
        parent = price_label.parent
        text = parent.get_text(strip=True)
        digits = re.sub(r'[^\d]', '', text)
        if digits:
            return int(digits)
            
    return None

def extract_details(soup):
    """Extract size, rooms, and district."""
    details = {
        'size_sqm': None,
        'rooms': None,
        'district': None,
        'address': None
    }
    
    # 1. Address/District from H1
    if soup.h1:
        h1_text = soup.h1.get_text(strip=True)
        details['address'] = h1_text
        # Try finding district (e.g., XIII. kerület)
        dist_match = re.search(r'([IVXLCDM]+)\.\s*kerület', h1_text, re.IGNORECASE)
        if dist_match:
            details['district'] = dist_match.group(1).upper()
            
    # 2. Main features (Size, Rooms)
    # Based on analysis: div with class containing 'fs-20' and 'fw-bold' often holds these
    feature_divs = soup.find_all('div', class_=lambda c: c and 'fs-20' in c and 'fw-bold' in c)
    
    for div in feature_divs:
        text = div.get_text(strip=True)
        
        # Size
        if 'm²' in text:
            match = re.search(r'(\d+)', text)
            if match:
                details['size_sqm'] = int(match.group(1))
        
        # Rooms
        elif 'szoba' in text.lower():
            # Handle "1 + 2 fél szoba" or "3 szoba"
            # Simple approach: sum all numbers found
            nums = re.findall(r'(\d+)', text)
            if nums:
               details['rooms'] = sum(map(int, nums))

    return details

def scrape_listing(url):
    """Scrapes a single listing page."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        # response.raise_for_status() # Don't raise, just log error for 404s
        
        if response.status_code != 200:
            logger.warning(f"Failed to load {url}, status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = extract_details(soup)
        data['price'] = extract_price(soup)
        data['url'] = url
        
        return data
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Scrape detailed sales data from Zenga links.')
    parser.add_argument('--input', type=str, required=True, help='Input CSV with links')
    parser.add_argument('--output', type=str, default='data/processed/zenga_sales_data.csv', help='Output CSV file')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of listings to scrape (for testing)')
    
    args = parser.parse_args()
    
    try:
        links_df = pd.read_csv(args.input)
        links = links_df['url'].tolist()
    except Exception as e:
        logger.error(f"Could not read input file: {e}")
        return

    if args.limit:
        links = links[:args.limit]
        
    logger.info(f"🚀 Starting to scrape {len(links)} listings...")
    
    results = []
    for i, url in enumerate(links):
        logger.info(f"[{i+1}/{len(links)}] Scraping: {url}")
        
        data = scrape_listing(url)
        if data:
            results.append(data)
            # Log progress
            if data['price'] and data['size_sqm']:
                 logger.info(f"   -> Price: {data['price']}, Size: {data['size_sqm']}m²")
            else:
                 logger.warning(f"   -> Missing data for {url}")
        
        time.sleep(1.5) # Polite delay
        
    # Save results
    if results:
        df = pd.DataFrame(results)
        
        # Determine price per sqm if possible
        if 'price' in df.columns and 'size_sqm' in df.columns:
            df['price_per_sqm'] = df.apply(
                lambda row: row['price'] / row['size_sqm'] if (pd.notnull(row['price']) and pd.notnull(row['size_sqm']) and row['size_sqm'] > 0) else None, 
                axis=1
            )
            
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df.to_csv(args.output, index=False)
        logger.info(f"✅ Saved {len(df)} listings to {args.output}")
    else:
        logger.warning("❌ No data scraped.")

if __name__ == "__main__":
    main()
