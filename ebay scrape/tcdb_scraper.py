import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict, Any
import random
import re

class TcdbScraper:
    def __init__(self):
        self.base_url = "https://www.tcdb.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    async def fetch_player_cards(self, player_name: str) -> List[Dict[str, Any]]:
        async with async_playwright() as p:
            # We use a persistent context to mimic a real user session better
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            try:
                # 2. Wait for Cloudflare/Page Load
                await asyncio.sleep(random.uniform(5, 8))
                
                # 3. Handle Cookie Consent in Iframes
                try:
                    # Look for consent button in all frames and main page
                    for frame in page.frames:
                        # Common Quantcast/SourcePoint selectors
                        for sel in ["button:has-text('Mindent elfogadok')", "button.sp_choice_type_11", "button[title='Mindent elfogadok']"]:
                            btn = await frame.query_selector(sel)
                            if btn and await btn.is_visible():
                                await btn.click()
                                print(f"Accepted cookies in frame using {sel}")
                                await asyncio.sleep(2)
                                break
                except: pass

                # 4. Search Results Handling
                try:
                    # Look for the first person profile link in search results
                    profile_link = await page.query_selector("a[href*='Person.cfm']")
                    if profile_link:
                        href = await profile_link.get_attribute("href")
                        # Construct direct Cards URL: /col/1/yea/0/ to show ALL cards
                        # Example: Person.cfm/pid/239181/Bukayo-Saka -> Person.cfm/pid/239181/col/1/yea/0/Bukayo-Saka
                        if "pid/" in href:
                            parts = href.split("/")
                            # Insert /col/1/yea/0/ after the PID
                            # parts: ['', 'Person.cfm', 'pid', '239181', 'Bukayo-Saka']
                            if len(parts) >= 5:
                                cards_url = f"{self.base_url}/Person.cfm/pid/{parts[3]}/col/1/yea/0/{parts[4]}"
                                print(f"Navigating to direct Cards URL: {cards_url}")
                                await page.goto(cards_url, wait_until="load")
                        else:
                            await profile_link.click()
                    else:
                        await page.goto(f"{self.base_url}/Search.cfm?SearchCategory=Soccer&q={player_name.replace(' ', '+')}")
                except Exception as e:
                    print(f"Navigation error: {e}")
                    pass

                # Wait for profile page load
                print("Waiting for cards table...")
                try:
                    await page.wait_for_selector("table.table-striped", timeout=10000)
                except:
                    print("Table not found. Checking if filters are needed.")

                # Debug snapshot
                await page.screenshot(path="tcdb_debug.png")
                with open("tcdb_debug.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                
                # Check for cards in the card table
                cards = []
                rows = await page.query_selector_all("tr")
                print(f"Analyzing {len(rows)} table rows...")
                
                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 3: continue
                    
                    card_text = await cells[1].inner_text()
                    attributes = await cells[2].inner_text()
                    
                    # Regex for Year and Card Number
                    # Example: "2019-20 Topps Chrome #72 Erling Haaland"
                    year_match = re.search(r"(\d{4}(?:-\d{2})?)", card_text)
                    number_match = re.search(r"#([\w-]+)", card_text)
                    
                    if year_match and player_name.lower() in card_text.lower():
                        year = year_match.group(1)
                        number = number_match.group(1) if number_match else ""
                        
                        # Clean up set name (remove year and player name)
                        set_name = card_text.replace(year, "").replace(player_name, "").replace("#"+number, "").strip()
                        set_name = re.sub(r"\s+", " ", set_name).strip()
                        
                        cards.append({
                            'year': year,
                            'set': set_name,
                            'number': number,
                            'rc': "RC" in attributes,
                            'player': player_name,
                            'raw_text': card_text
                        })
                
                return cards
            except Exception as e:
                print(f"Error: {e}")
                return []
            finally:
                await browser.close()

async def main():
    scraper = TcdbScraper()
    cards = await scraper.fetch_player_cards("Erling Haaland")
    print(f"Found {len(cards)} cards.")
    for c in cards[:3]:
        print(f"- {c['raw_text']}")

if __name__ == "__main__":
    asyncio.run(main())
