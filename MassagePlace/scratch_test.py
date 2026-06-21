import sys
import time
from playwright.sync_api import sync_playwright

def run():
    print("Starting Playwright...", flush=True)
    with sync_playwright() as p:
        print("Launching Chromium (headless=True)...", flush=True)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # Go to a query search directly
        query = "massage Budapest VII. district"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/"
        print(f"Navigating to: {url}", flush=True)
        page.goto(url)
        
        # Wait a bit to see if we hit consent
        print("Waiting for page load...", flush=True)
        page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"Current URL: {current_url}", flush=True)
        page.screenshot(path="screenshot_initial.png")
        print("Saved screenshot_initial.png", flush=True)
        
        # Let's check for consent buttons
        print("Checking for consent dialog...", flush=True)
        consent_buttons = page.locator("button").all()
        print(f"Found {len(consent_buttons)} buttons total on the page.", flush=True)
        for i, btn in enumerate(consent_buttons):
            text = btn.inner_text().strip()
            if text:
                print(f"Button {i}: {text}", flush=True)
                # Check for consent text (Hungarian or English)
                if any(x in text.lower() for x in ["accept all", "elfogad", "mindent elfogad", "összes elfogadása"]):
                    print(f" Clicking consent button: {text}", flush=True)
                    try:
                        btn.click()
                        print("Clicked! Waiting for redirection...", flush=True)
                        page.wait_for_timeout(3000)
                        print(f"New URL after consent: {page.url}", flush=True)
                        page.screenshot(path="screenshot_after_consent.png")
                        break
                    except Exception as e:
                        print(f"Error clicking button: {e}", flush=True)
        
        # If still on consent page, try clicking buttons with specific text
        if "consent" in page.url:
            print("Still on consent page. Let's try more direct selectors...", flush=True)
            # Try to click any button that has "Accept all" or "Elfogadom"
            for term in ["Accept all", "Elfogadom", "Mindent elfogadok", "Az összes elfogadása"]:
                try:
                    loc = page.get_by_role("button", name=term, exact=False)
                    if loc.count() > 0:
                        print(f"Found button with name '{term}'. Clicking...", flush=True)
                        loc.first.click()
                        page.wait_for_timeout(3000)
                        print(f"URL after name click '{term}': {page.url}", flush=True)
                        page.screenshot(path="screenshot_after_consent_name.png")
                        break
                except Exception as e:
                    print(f"Error clicking term {term}: {e}", flush=True)
                    
        print(f"Final URL: {page.url}", flush=True)
        
        # Let's wait for results to load
        print("Waiting for search results feed...", flush=True)
        page.wait_for_timeout(5000)
        page.screenshot(path="screenshot_results_loaded.png")
        print("Saved screenshot_results_loaded.png", flush=True)
        
        # Check all links
        links = page.locator("a").all()
        place_links = []
        for link in links:
            href = link.get_attribute("href")
            if href and "/maps/place/" in href:
                place_links.append(href)
        
        if place_links:
            test_link = place_links[0]
            print(f"Opening test link for detail scraping: {test_link}", flush=True)
            # Create a new page to keep search list
            detail_page = context.new_page()
            detail_page.goto(test_link)
            print("Waiting for detail page to load...", flush=True)
            detail_page.wait_for_timeout(5000)
            detail_page.screenshot(path="screenshot_detail_page.png")
            print("Saved screenshot_detail_page.png", flush=True)
            
            def clean_str(s):
                if not s:
                    return ""
                # Keep alphanumeric, standard symbols, and hungarian accents, remove odd icons
                return "".join(c for c in s if ord(c) < 65533 and ord(c) not in [0xe5d4, 0xe878])
            
            # Print title
            h1s = detail_page.locator("h1").all()
            for idx, h in enumerate(h1s):
                print(f"H1 {idx}: {clean_str(h.inner_text())}", flush=True)
                
            # Let's check for links on the details page
            detail_links = detail_page.locator("a").all()
            for idx, l in enumerate(detail_links):
                href = l.get_attribute("href") or ""
                item_id = l.get_attribute("data-item-id") or ""
                aria_label = l.get_attribute("aria-label") or ""
                text = l.inner_text().strip().replace('\n', ' ')
                
                # Check if it looks like a website, phone or address
                is_rel = False
                if "http" in href and "google.com" not in href:
                    is_rel = True
                if "authority" in item_id or "phone" in item_id or "address" in item_id:
                    is_rel = True
                if "webhely" in aria_label.lower() or "website" in aria_label.lower() or "telefon" in aria_label.lower():
                    is_rel = True
                    
                if is_rel:
                    print(f"LINK: text='{clean_str(text)}', href='{href}', data-item-id='{item_id}', aria-label='{clean_str(aria_label)}'", flush=True)
            
            # Let's check for buttons
            detail_buttons = detail_page.locator("button").all()
            for idx, b in enumerate(detail_buttons):
                item_id = b.get_attribute("data-item-id") or ""
                aria_label = b.get_attribute("aria-label") or ""
                text = b.inner_text().strip().replace('\n', ' ')
                
                is_rel = False
                if "authority" in item_id or "phone" in item_id or "address" in item_id:
                    is_rel = True
                if "webhely" in aria_label.lower() or "website" in aria_label.lower() or "telefon" in aria_label.lower() or "cím" in aria_label.lower() or "address" in aria_label.lower():
                    is_rel = True
                # Let's check if the text contains a Hungarian zip code pattern like 4 digits (e.g. 1074)
                import re
                if re.search(r'\b\d{4}\b', text):
                    is_rel = True
                    
                if is_rel:
                    print(f"BUTTON: text='{clean_str(text)}', data-item-id='{item_id}', aria-label='{clean_str(aria_label)}'", flush=True)
                    
            # Let's inspect address
            address_elements = detail_page.locator("[data-item-id*='address']").all()
            for idx, el in enumerate(address_elements):
                print(f"Address Element {idx}: text='{clean_str(el.inner_text())}'", flush=True)
                
            detail_page.close()
        else:
            print("No place links found to test detail scraping.", flush=True)

        browser.close()

if __name__ == "__main__":
    run()
