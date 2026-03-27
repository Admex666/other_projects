import os
import sys
import time
import random
import statistics

# Add root directoy to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ebay_scraper import EbayScraper

def test_ebay_speed():
    scraper = EbayScraper()
    queries = ["Erling Haaland", "Lamine Yamal", "Pau Cubarsi", "Jude Bellingham", "Kylian Mbappe"]
    
    print(f"--- Starting eBay Speed Test ---")
    times = []
    
    for q in queries:
        start = time.time()
        print(f"Scraping: {q}...", end="", flush=True)
        items = scraper.fetch_sold_items(q, pages=1)
        end = time.time()
        duration = end - start
        times.append(duration)
        print(f" Done ({duration:.2f}s, found {len(items)} items)")
        # Small delay to mimic real usage and avoid rate limits
        time.sleep(random.uniform(0.5, 1.0))
        
    avg = sum(times) / len(times)
    median = statistics.median(times)
    
    print(f"\n--- Results ---")
    print(f"Average time per page: {avg:.2f}s")
    print(f"Median time per page: {median:.2f}s")
    print(f"Throughput: ~{60/avg:.1f} pages/min")

if __name__ == "__main__":
    test_ebay_speed()
