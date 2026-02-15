"""
Optimized Selenium scraper for Zenga.hu rental listings.

This module provides classes and functions for efficient web scraping
of real estate listings with parallel processing and caching.
"""

import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


class OptimizedSeleniumScraper:
    """Optimized Selenium scraper with parallel processing support."""
    
    def __init__(self, max_workers: int = 8):
        """
        Initialize the scraper.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.drivers = []
    
    def setup_driver(self):
        """
        Setup optimized Chrome driver with headless mode and performance settings.
        
        Returns:
            WebDriver instance or None if setup failed
        """
        options = webdriver.ChromeOptions()
        
        # Performance optimizations
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        
        # Speed optimizations
        options.add_argument("--disable-images")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-java")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Memory optimization
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # Network optimization
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-background-networking")
        
        # Page load strategy
        options.page_load_strategy = 'none'
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            driver.set_page_load_timeout(10)
            driver.implicitly_wait(2)
            return driver
        except Exception as e:
            print(f"❌ Driver creation error: {e}")
            return None
    
    def extract_number(self, text: str) -> Optional[float]:
        """
        Extract numerical value from text string.
        
        Args:
            text: String containing numbers
            
        Returns:
            Extracted float value or None
        """
        if not text or pd.isna(text):
            return None
        text = str(text).replace("\xa0", "").replace(".", "").replace(" ", "")
        match = re.search(r'(\d+,?\d*)', text)
        return float(match.group(1).replace(",", ".")) if match else None
    
    def smart_wait(self, driver, selector: str, timeout: int = 3) -> bool:
        """
        Smart wait for element presence.
        
        Args:
            driver: WebDriver instance
            selector: CSS selector
            timeout: Wait timeout in seconds
            
        Returns:
            True if element found, False otherwise
        """
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return True
        except:
            return False
    
    def scrape_listing(self, url: str, driver, listing_type: str = "rental") -> Optional[Dict]:
        """
        Scrape single listing details using optimized method.
        
        Args:
            url: Listing URL
            driver: WebDriver instance
            listing_type: 'rental' or 'sale' - affects data extraction
            
        Returns:
            Dictionary with listing data or None
        """
        try:
            # Fast navigation
            driver.get(url)
            
            # Minimal wait for key element
            if not self.smart_wait(driver, 'h1[data-id="h1"]', timeout=5):
                return None
            
            listing_data = {"url": url}
            
            # Fast data extraction
            selectors = {
                "title": 'h1[data-id="h1"]',
                "price": 'div.fc-black-2.fs-32.fw-900',
                "area_m2": 'div[data-cy="advert-details-first-param"]',
                "floor": 'div[data-cy="advert-details-third-param"]',
                "rooms": 'div[data-cy="advert-details-second-param"]',
                "location": 'button[data-cy="advert-map-map-btn"] span.fs-16',
            }
            
            # Extract all elements
            for field, selector in selectors.items():
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    
                    if field in ["price", "area_m2", "rooms"]:
                        listing_data[field] = self.extract_number(text)
                    else:
                        listing_data[field] = text
                except:
                    listing_data[field] = None
            
            # Extract additional properties
            try:
                items = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="advert-details-param-list-item"]')
                for item in items[:15]:  # Increased limit specifically for sales
                    try:
                        key = item.find_element(By.CSS_SELECTOR, 'span').text.strip().replace(":", "")
                        val = item.find_element(By.CSS_SELECTOR, '.fw-bold').text.strip()
                        if key and key.strip():
                            listing_data[key] = val
                    except:
                        continue
            except:
                pass
            
            listing_data["scrape_date"] = datetime.now().strftime('%Y-%m-%d')
            listing_data["listing_type"] = listing_type
            return listing_data
            
        except Exception as e:
            print(f"❌ Error processing {url}: {str(e)}")
            return None


class CacheManager:
    """Manage processed URLs cache to avoid redundant scraping."""
    
    def __init__(self, cache_file: str = "cache/scrape_cache_rentals.json"):
        """
        Initialize cache manager.
        
        Args:
            cache_file: Path to cache file
        """
        self.cache_file = cache_file
    
    def load_cache(self) -> Dict:
        """
        Load cache from file.
        
        Returns:
            Dictionary with processed URLs
        """
        if os.path.exists(self.cache_file):
            with open(self.cache_file) as f:
                return json.load(f)
        return {"processed_urls": []}
    
    def save_cache(self, urls: List[str]):
        """
        Save processed URLs to cache.
        
        Args:
            urls: List of processed URLs
        """
        cache = self.load_cache()
        cache["processed_urls"].extend(urls)
        cache["processed_urls"] = list(set(cache["processed_urls"]))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)


def process_batch(
    urls: List[str], 
    existing_urls: set, 
    max_workers: int = 8,
    listing_type: str = "rental"
) -> List[Dict]:
    """
    Process URLs in parallel with multiple drivers.
    
    Args:
        urls: List of URLs to process
        existing_urls: Set of already processed URLs
        max_workers: Number of parallel workers
        listing_type: 'rental' or 'sale'
        
    Returns:
        List of scraped listing dictionaries
    """
    scraper = OptimizedSeleniumScraper(max_workers)
    results = []
    
    # Filter only new URLs
    urls_to_process = [url for url in urls if url not in existing_urls and not pd.isna(url)]
    
    if not urls_to_process:
        return []
    
    # Create driver pool
    drivers = []
    for _ in range(max_workers):
        driver = scraper.setup_driver()
        if driver:
            drivers.append(driver)
    
    if not drivers:
        print("❌ Failed to create drivers!")
        return []
    
    print(f"🚀 {len(drivers)} drivers created, processing {len(urls_to_process)} URLs...")
    
    try:
        with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
            # Distribute tasks
            futures = []
            for i, url in enumerate(urls_to_process):
                driver = drivers[i % len(drivers)]
                future = executor.submit(scraper.scrape_listing, url, driver, listing_type)
                futures.append(future)
                
                # Small delay to avoid overwhelming
                time.sleep(random.uniform(0.05, 0.15))
            
            # Collect results with progress bar
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Processing {listing_type}s"):
                result = future.result()
                if result:
                    results.append(result)
    
    finally:
        # Close drivers
        for driver in drivers:
            try:
                driver.quit()
            except:
                pass
    
    return results
