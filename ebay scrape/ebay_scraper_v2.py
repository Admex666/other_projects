import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict, Any
import re
import random

class EbayScraperV2:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    async def fetch_sold_items(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        async with async_playwright() as p:
            # Persistent context helps bypass robot checks by saving session data
            user_data_dir = "./ebay_user_data"
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                user_agent=random.choice(self.user_agents),
                locale="en-US",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.pages[0] if context.pages else await context.new_page()
            
            try:
                # 1. established session
                if not context.cookies():
                    print("Establishing new session...")
                    await page.goto("https://www.ebay.com", wait_until="load")
                    await asyncio.sleep(random.uniform(5, 8))
                
                # 2. Search
                search_url = f"{self.base_url}?_nkw={query.replace(' ', '+')}&_sacat=0&LH_Sold=1&LH_Complete=1&_ipg=100&_stpos=10001&_gbe=1"
                print(f"Searching for sold items: {search_url}")
                await page.goto(search_url, wait_until="load")
                
                # Wait for listings (handling challenge)
                try:
                    await page.wait_for_selector("li.s-item", timeout=15000)
                except:
                    print("Listings not found immediately, checking for challenge or consent...")
                    await page.screenshot(path="ebay_v2_debug.png")
                
                # 3. Handle Cookie Consent (Hungarian: "Összes elfogadása")
                try:
                    consent_btn = await page.get_by_text("Összes elfogadása").first
                    if await consent_btn.is_visible():
                        await consent_btn.click()
                        await asyncio.sleep(2)
                except: pass

                items = []
                listings = await page.query_selector_all("li.s-item")
                print(f"Found {len(listings)} listings.")
                
                for listing in listings:
                    # Previous selectors from subagent
                    title_el = await listing.query_selector(".s-item__title")
                    price_el = await listing.query_selector(".s-item__price")
                    
                    if title_el and price_el:
                        title = await title_el.inner_text()
                        if "Shop on eBay" in title or "New Listing" in title:
                            # Clean "New Listing" prefix
                            title = title.replace("New Listing", "").strip()
                        
                        if not title or title.lower() == "shop on ebay": continue
                        
                        price_text = await price_el.inner_text()
                        # Extract first price found
                        price_match = re.search(r"[\d,.]+", price_text)
                        if price_match:
                            price = float(price_match.group(0).replace(",", ""))
                            items.append({
                                'title': title,
                                'price': price,
                                'currency': 'USD' if '$' in price_text else 'HUF' if 'HUF' in price_text else 'Unknown',
                                'query': query
                            })
                        
                    if len(items) >= limit:
                        break
                
                return items
            except Exception as e:
                print(f"Error: {e}")
                return []
            finally:
                await browser.close()

async def main():
    scraper = EbayScraperV2()
    items = await scraper.fetch_sold_items("Erling Haaland 2019 Topps Chrome Sapphire", limit=10)
    print(f"Found {len(items)} sold items.")
    for it in items[:5]:
        print(f"- {it['title']} | Price: {it['price']} {it['currency']}")

if __name__ == "__main__":
    asyncio.run(main())
