import time
import re
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
from typing import Optional, List, Dict

def get_all_stays(city, country, start_date, end_date, 
                  rooms=1, adults=2, children=0,
                  price_min=0, price_max=9007199254740991,
                  min_rating=0,
                  accommodation_types=None,
                  amenities=None,
                  breakfast=False,
                  progress_callback=None):
    """Scrapes accommodation data from cozycozy.com."""
    
    # Type kódok mapping
    if accommodation_types is None:
        combined_types = ["$HOTEL", "$VR", "$HOSTEL", "$GUEST", "$OOO", "$CAMPING"]
    else:
        combined_types = [f"${t.upper()}" for t in accommodation_types]

    # Kényelmi szolgáltatások mapping (Frontend CODE -> CozyCozy API CODE)
    amenity_mapping = {
        "WIFI": "INTERNET",
        "POOL": "SWIMPOOL",
        "PARKING": "FREEPARK",
        "AC": "AIRCOND",
        "KITCHEN": "KITCHEN"
    }

    if amenities is None:
        amenity_codes = []
    else:
        # Mapping alkalmazása: csak azokat vesszük át, amikhez van kódunk
        amenity_codes = [amenity_mapping[a.upper()] for a in amenities if a.upper() in amenity_mapping]

    def build_filter_string(price_min, price_max, min_rating, accommodation_types, amenities, breakfast):
        filters = []
        if price_min > 0 or price_max < 9007199254740991:
            filters.append(f"p:{price_min},{price_max}")
        if min_rating > 0:
            filters.append(f"r:{min_rating}")
        if accommodation_types:
            type_str = ','.join([f"${t}" for t in accommodation_types])
            filters.append(f"t:{type_str}")
        if amenities:
            amenity_str = ','.join(amenities)
            filters.append(f"a:{amenity_str}")
        if breakfast:
            filters.append("b:1")
        return ';'.join(filters)

    COUNTRY_TRANSLATIONS = {
        "magyarország": "Hungary", "spanyolország": "Spain", "olaszország": "Italy",
        "franciaország": "France", "németország": "Germany", "ausztria": "Austria",
        "egyesült királyság": "United Kingdom", "anglia": "United Kingdom",
        "görögország": "Greece", "horvátország": "Croatia", "portugália": "Portugal",
        "hollandia": "Netherlands", "svájc": "Switzerland", "lengyelország": "Poland",
        "csehország": "Czech Republic", "ciprus": "Cyprus", "málta": "Malta",
        "törökország": "Turkey", "thaiföld": "Thailand", "egyesült államok": "United States"
    }
    
    clean_country = country.strip()
    normalized_country = COUNTRY_TRANSLATIONS.get(clean_country.lower(), clean_country)

    encoded_city = urllib.parse.quote(city.strip())
    encoded_country = urllib.parse.quote(normalized_country)

    filter_string = build_filter_string(price_min, price_max, min_rating, 
                                        accommodation_types, amenities, breakfast)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Modern headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Képek letiltása
    chrome_options.add_argument("--disk-cache-size=1") # Cache minimalizálás
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.page_load_strategy = 'eager'

    driver = None
    try:
        print("[INFO] Chrome indítása (Optimized)...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Bypass detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        if progress_callback: progress_callback(5)
    except Exception as e:
        print(f"[ERROR] CRITICAL: Chrome indítás sikertelen: {e}")
        return {"entries": [], "error": f"Böngésző indítási hiba (RAM?): {str(e)}"}
    
    try:
        # Base URL without filters first (we just need the searchId)
        base_url = f"https://www.cozycozy.com/en/search/{encoded_city}%2C%20{encoded_country}/{start_date}/{end_date}/{rooms}-{adults}-{children}/results"
        print(f"[INFO] Cozycozy megnyitása: {base_url}")
        driver.get(base_url)
        if progress_callback: progress_callback(10)
        
        # Wait for the results links with searchId - selector frissítve
        elem = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='searchId=']"))
        )

        found = False
        search_id = None
        for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='searchId=']"):
            href = link.get_attribute("href")
            if "searchId=" in href:
                match = re.search(r"searchId=([A-Za-z0-9]+)", href)
                if match:
                    search_id = match.group(1)
                    found = True
                    break

        if not found:
            print("⚠️ searchId not found within timeout.")
            return {"entries": [], "error": "Időtúllépés: A szálláskereső oldal nem töltött be időben (searchId hiányzik)."}

        if progress_callback: progress_callback(20)

        # Pagination logic
        all_results = []
        offset = 0
        limit = 1500 # Megnövelt limit a teljes Cozycozy kínálat lefedéséhez
        batch_size = 100
        
        while offset < limit:
            # API call via script execution
            api_call_script = f"""
            return fetch('https://www.cozycozy.com/api/getResultList', {{
                method: 'POST',
                headers: {{
                    'accept': 'application/json, text/plain, */*',
                    'content-type': 'application/json',
                    'x-search-id': '{search_id}',
                    'x-split-id': '0'
                }},
                body: JSON.stringify({{
                    searchId: '{search_id}',
                    sorting: 'ranking',
                    offset: {offset},
                    count: {batch_size},
                    filters: {{
                        bounds: null,
                        noBounds: true,
                        price: [{price_min}, {price_max}],
                        instantBooking: false,
                        combinedTypeCodes: {json.dumps(combined_types)},
                        starRatings: [],
                        minRating: {min_rating},
                        ratingRequired: {str(min_rating > 0).lower()},
                        amenityCodes: {json.dumps(amenity_codes)},
                        providerCodes: [],
                        minBedRoomCount: 1,
                        minBathRoomCount: 0,
                        cityCodes: [],
                        areaCodes: [],
                        minResponseTime: null,
                        updateBounds: true,
                        breakfast: {str(breakfast).lower()},
                        minCancellationCategory: 0
                    }},
                    estimateBounds: {{
                        targetSize: {{ width: 1136, height: 925 }}
                    }},
                    prefixAccommodationIds: [],
                    processNewResults: true,
                    columnCount: 3,
                    excludeAds: false
                }})
            }}).then(response => response.json());
            """
            
            try:
                # Add a small delay between batches
                if offset > 0:
                    time.sleep(0.3)
                    
                batch_results = driver.execute_script(api_call_script)
                
                if not batch_results or 'entries' not in batch_results or not batch_results['entries']:
                    break
                    
                all_results.extend(batch_results['entries'])
                
                if len(batch_results['entries']) < batch_size:
                    break
                    
                offset += batch_size
                
                # Update progress: Map offset (0-1500) to percentage (20-90)
                if progress_callback:
                    p = 20 + int((offset / limit) * 70)
                    progress_callback(min(p, 90))
                
            except Exception as e:
                print(f"Error fetching batch at offset {offset}: {e}")
                break

        if not all_results:
             print("⚠️ No results scraped.")
             # Nem hiba, csak 0 találat
             return {"entries": []}

        return {"entries": all_results}

    except Exception as e:
        print(f"❌ Error during scraping logic: {e}")
        return {"entries": [], "error": f"Hiba az adatgyűjtés közben: {str(e)}"}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def parse_distance(location_text):
    """Helper to parse distance from center (e.g., '2 km from the city center')."""
    if not location_text:
        return 10.0 # Default fallback distance
    match = re.search(r"([\d\.]+)\s*km", location_text)
    if match:
        return float(match.group(1))
def clean_hotel_booking_url(raw_url: Optional[str], hotel_name: str = "", city_name: str = "") -> str:
    """
    Kitisztítja a Cozycozy által visszaadott szállás linkeket:
    1. Kibontja az affiliate wrappereket (pl. prf.hn destination: paraméter, Cozycozy /redirect?to=).
    2. Eltávolítja a Booking.com-ot átirányító törött tokeneket (%CLICK_ID%).
    3. Ha nem közvetlen szálláslink, intelligensen a konkrét szálláskeresésre irányít.
    """
    if not raw_url or raw_url == '#' or raw_url == 'None':
        if hotel_name:
            q = urllib.parse.quote(f"{hotel_name} {city_name}".strip())
            return f"https://www.google.com/search?q={q}+booking"
        return "#"
        
    url = raw_url.strip()
    
    # 0. Localhost prefix eltávolítása (ha van)
    if "localhost:8000/" in url:
        url = url.split("localhost:8000/")[-1]

    # 1. Affiliate wrapperek kibontása (destination: vagy to= paraméter)
    if "destination:" in url:
        parts = url.split("destination:")
        if len(parts) > 1:
            url = parts[1]
    elif "to=" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if "to" in params and params["to"]:
                url = params["to"][0]
        except:
            pass

    # 2. Rekurzív unquote (többszörösen kódolt URL-ek kibontása)
    for _ in range(3):
        try:
            decoded = urllib.parse.unquote(url)
            if decoded == url:
                break
            url = decoded
        except:
            break

    # 3. Ha az unquote után újabb destination: bukkant fel
    if "destination:" in url:
        parts = url.split("destination:")
        if len(parts) > 1:
            url = parts[1]

    url = url.strip()

    # 4. Törött macro tokenek eltávolítása (ezek miatt dob a Booking a főoldalra)
    url = re.sub(r'%25CLICK_ID%25|%CLICK_ID%|%click_id%', '', url)
    url = re.sub(r'([?&])label=(?:&|$)', r'\1', url)
    url = re.sub(r'[?&]$', '', url)

    # 5. Protokoll ellenőrzése
    if not url.startswith('http'):
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('www.'):
            url = 'https://' + url
        elif '.' in url and '/' in url:
            url = 'https://' + url.lstrip('/')

    # 6. Ha általános Booking keresési URL érkezett konkrét szállás ID nélkül
    if 'booking.com/searchresults' in url and 'hotel/' not in url:
        if hotel_name:
            q_hotel = urllib.parse.quote(hotel_name)
            q_city = urllib.parse.quote(city_name) if city_name else ""
            url = f"https://www.booking.com/searchresults.html?ss={q_hotel}&ssne={q_city}"

    return url

def parse_accommodation_results(results):
    """Converts Cozycozy API JSON response to a structured list of dictionaries."""
    if not results or 'entries' not in results:
        return []
    
    parsed_data = []
    seen_hotels = set() # Duplikátum szűréshez: (név, rating) páros alapú
    
    for entry in results['entries']:
        highlighted = entry.get('highlightedResults', [])
        if not highlighted:
            continue
            
        cheapest = min(highlighted, key=lambda x: x.get('eurPricePerNight', float('inf')))
        provider = cheapest.get('providerName', '')
        
        # [CONSTRAINT] Filter out Hostelworld
        if 'hostelworld' in provider.lower():
            continue

        name = entry.get('name', '').strip()
        rating = entry.get('ratingScore') or 0
        
        # Duplikátum szűrés: Ha ugyanaz a név és rating, akkor valószínűleg ugyanaz a szállás
        match_key = (name.lower(), rating)
        if match_key in seen_hotels:
            continue
        seen_hotels.add(match_key)

        amenities = entry.get('amenityCodes', [])
        acc_type = entry.get('typeCode', 'UNKNOWN') 

        base_info = {
            'id': entry.get('accommodationId'),
            'name': name,
            'title': entry.get('title'),
            'city': entry.get('cityName'),
            'rating_score': rating,
            'rating_count': entry.get('ratingCount') or 0,
            'location_text': entry.get('locationText'),
            'distance_km': parse_distance(entry.get('locationText')),
            'latitude': entry.get('coordinates', {}).get('latitude'),
            'longitude': entry.get('coordinates', {}).get('longitude'),
            'instant_booking': entry.get('instantBooking', False),
            'amenities': amenities,
            'accommodation_type': acc_type
        }
        
        booking_url = clean_hotel_booking_url(cheapest.get('deeplinkUrl'), name, base_info.get('city') or '')

        base_info.update({
            'price_per_night_eur': cheapest.get('eurPricePerNight'),
            'total_price': cheapest.get('totalPrice', {}).get('value'),
            'currency': cheapest.get('totalPrice', {}).get('currencyCode'),
            'provider': provider,
            'booking_url': booking_url,
            'room_type': cheapest.get('text'),
        })
        
        thumbnails = entry.get('lightThumbnails', {})
        first_urls = thumbnails.get('firstUrls', [])
        base_info['image_url'] = first_urls[0] if first_urls else None
        
        if 'price_per_night_eur' in base_info:
            parsed_data.append(base_info)
            
    return parsed_data

import random

def generate_mock_stays(city, country, count=30):
    """Generates realistic mock accommodation data when scraping fails."""
    print(f"Generating {count} mock stays for {city}, {country}")
    
    mock_data = []
    types = ["$HOTEL", "$VR", "$HOSTEL", "$GUEST"]
    amenities_list = ["WIFI", "AC", "POOL", "PARKING", "KITCHEN"]
    
    for i in range(count):
        price = random.randint(30, 300)
        rating = round(random.uniform(3.5, 5.0), 1)
        
        entry = {
            "accommodationId": f"mock_{i}",
            "name": f"Hotel {city} {i+1}",
            "title": f"Nice Stay in {city}",
            "cityName": city,
            "ratingScore": rating,
            "ratingCount": random.randint(10, 1000),
            "locationText": f"{round(random.uniform(0.5, 5.0), 1)} km from center",
            "coordinates": {"latitude": 0, "longitude": 0},
            "instantBooking": True,
            "amenityCodes": random.sample(amenities_list, k=random.randint(2, 5)),
            "typeCode": random.choice(types),
            "highlightedResults": [{
                "eurPricePerNight": price,
                "totalPrice": {"value": price * 3, "currencyCode": "EUR"},
                "providerName": "Booking.com" if i % 2 == 0 else "Airbnb",
                "deeplinkUrl": "#",
                "text": "Standard Room"
            }],
            "lightThumbnails": {
                "firstUrls": ["https://via.placeholder.com/300x200?text=Hotel+Mock"]
            }
        }
        mock_data.append(entry)
        
    return {"entries": mock_data, "is_mock": True}
