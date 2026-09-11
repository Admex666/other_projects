"""
Google Maps Places Scraper Connector
Implements automated browser scraping (via Playwright) modeled after open-source tools like gosom/google-maps-scraper,
extracting place names, ratings, review counts, categories, and coordinates without requiring a paid API key.
"""
import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseConnector, DestinationSeed, RawSourceRecord

class GoogleMapsConnector(BaseConnector):
    def __init__(self, parser_version: str = "v1.0", timeout_sec: int = 30):
        super().__init__(name="google_maps", license_name="Proprietary / Web Data", parser_version=parser_version)
        self.timeout_sec = timeout_sec

    def fetch_records(self, seed: DestinationSeed, limit: int = 25) -> List[RawSourceRecord]:
        """Scrapes Google Maps search results for attractions & experiences in destination."""
        # 1. Check if official API key is provided for faster direct REST execution
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            return self._fetch_via_places_api(seed, api_key, limit)

        # 2. Otherwise run open browser scraper
        return self._fetch_via_playwright(seed, limit)

    def _fetch_via_places_api(self, seed: DestinationSeed, api_key: str, limit: int) -> List[RawSourceRecord]:
        import requests
        records: List[RawSourceRecord] = []
        now_iso = datetime.utcnow().isoformat()
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{seed.lat},{seed.lon}",
                "radius": int(seed.radius_km * 1000),
                "type": "tourist_attraction",
                "key": api_key
            }
            resp = requests.get(url, params=params, timeout=self.timeout_sec)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", [])[:limit]:
                    records.append(RawSourceRecord(
                        source=self.name,
                        source_id=item.get("place_id", ""),
                        destination_id=seed.destination_id,
                        name_candidate=item.get("name", ""),
                        raw_payload=item,
                        license=self.license_name,
                        retrieved_at=now_iso,
                        parser_version=self.parser_version
                    ))
        except Exception as e:
            print(f"[GOOGLE MAPS API WARN] Direct Places API failed: {e}")
        return records

    def _fetch_via_playwright(self, seed: DestinationSeed, limit: int) -> List[RawSourceRecord]:
        import asyncio
        from playwright.sync_api import sync_playwright

        records: List[RawSourceRecord] = []
        now_iso = datetime.utcnow().isoformat()
        search_query = f"top tourist attractions in {seed.name} {seed.country}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}/@{seed.lat},{seed.lon},13z?hl=en"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    locale="en-US"
                )
                page = context.new_page()
                page.goto(url, timeout=self.timeout_sec * 1000, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)

                # Consent handle (Google GDPR modal)
                try:
                    consent_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree'), form:has(button) button:visible").first
                    if consent_btn.is_visible():
                        consent_btn.click()
                        page.wait_for_timeout(1500)
                except Exception:
                    pass

                # Scroll the feed panel to load more items
                try:
                    feed = page.locator("div[role='feed']")
                    if feed.is_visible():
                        scroll_count = min(max(limit // 5, 3), 8)
                        for _ in range(scroll_count):
                            feed.evaluate("el => el.scrollBy(0, 2000)")
                            page.wait_for_timeout(1200)
                except Exception:
                    pass

                # Extract place anchors and cards
                places_data = page.evaluate("""() => {
                    const results = [];
                    // Pattern 1: feed links with aria-label
                    const anchors = document.querySelectorAll("div[role='feed'] a[aria-label], a[href*='/maps/place/']");
                    const seen = new Set();
                    
                    for (const a of anchors) {
                        const name = a.getAttribute('aria-label') || a.innerText;
                        const href = a.getAttribute('href') || '';
                        if (!name || name.length < 3 || seen.has(name)) continue;
                        seen.add(name);

                        // Look up container card for rating and reviews
                        const card = a.closest("div[jsaction]") || a.parentElement;
                        let rating = null;
                        let reviewCount = null;
                        let category = null;

                        if (card) {
                            const text = card.innerText || '';
                            const rateMatch = text.match(/([1-5]\\.[0-9])/);
                            if (rateMatch) rating = parseFloat(rateMatch[1]);
                            
                            const revMatch = text.match(/\\(([0-9,.]+)\\)/);
                            if (revMatch) reviewCount = parseInt(revMatch[1].replace(/[,.]/g, ''), 10);
                        }

                        // Try to extract lat/lon from URL
                        let lat = null;
                        let lon = null;
                        const coordMatch = href.match(/!3d([0-9.-]+)!4d([0-9.-]+)/) || href.match(/@([0-9.-]+),([0-9.-]+)/);
                        if (coordMatch) {
                            lat = parseFloat(coordMatch[1]);
                            lon = parseFloat(coordMatch[2]);
                        }

                        results.push({
                            name: name.trim(),
                            href: href,
                            rating: rating,
                            review_count: reviewCount,
                            category: category,
                            lat: lat,
                            lon: lon
                        });
                    }
                    return results;
                }""")

                browser.close()

                for p_item in places_data[:limit]:
                    name = p_item.get("name")
                    if not name:
                        continue
                    
                    href = p_item.get("href", "")
                    # Extract place ID or slug from href
                    slug_match = re.search(r'/maps/place/([^/]+)', href)
                    source_id = slug_match.group(1) if slug_match else name.replace(" ", "_").lower()

                    records.append(RawSourceRecord(
                        source=self.name,
                        source_id=source_id,
                        destination_id=seed.destination_id,
                        name_candidate=name,
                        raw_payload=p_item,
                        license=self.license_name,
                        retrieved_at=now_iso,
                        parser_version=self.parser_version
                    ))

        except Exception as e:
            print(f"[GOOGLE MAPS SCRAPER ERROR] Playwright scraping failed: {e}")

        return records
