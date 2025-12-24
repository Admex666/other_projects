import time
import re
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_all_stays(city, country, start_date, end_date, 
                  rooms=1, adults=2, children=0,
                  price_min=0, price_max=9007199254740991,
                  min_rating=0,
                  accommodation_types=None,
                  amenities=None,
                  breakfast=False):
    """Scrapes accommodation data from cozycozy.com."""
    
    # Type kódok mapping
    if accommodation_types is None:
        combined_types = ["$HOTEL", "$VR", "$HOSTEL", "$GUEST", "$OOO", "$CAMPING"]
    else:
        combined_types = [f"${t.upper()}" for t in accommodation_types]

    if amenities is None:
        amenity_codes = []
    else:
        amenity_codes = [a.upper() for a in amenities]

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

    filter_string = build_filter_string(price_min, price_max, min_rating, 
                                        accommodation_types, amenities, breakfast)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        base_url = f"https://www.cozycozy.com/en/search/{city}%2C%20{country}/{start_date}/{end_date}/{rooms}-{adults}-{children}/results"
        url = f"{base_url}?filters={filter_string}" if filter_string else base_url
        
        driver.get(url)
        
        # Wait for the results to start loading
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.m-card-button"))
        )

        found = False
        search_id = None
        for link in driver.find_elements(By.CSS_SELECTOR, "a.m-card-button"):
            href = link.get_attribute("href")
            if "searchId=" in href:
                match = re.search(r"searchId=([A-Za-z0-9]+)", href)
                if match:
                    search_id = match.group(1)
                    found = True
                    break

        if not found:
            return {"entries": [], "error": "searchId not found"}

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
                offset: 0,
                count: 100,
                filters: {{
                    bounds: null,
                    noBounds: true,
                    price: [{price_min}, {price_max}],
                    instantBooking: true,
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
        results = driver.execute_script(api_call_script)
        return results

    finally:
        driver.quit()

def parse_distance(location_text):
    """Helper to parse distance from center (e.g., '2 km from the city center')."""
    if not location_text:
        return 10.0 # Default fallback distance
    match = re.search(r"([\d\.]+)\s*km", location_text)
    if match:
        return float(match.group(1))
    return 10.0

def parse_accommodation_results(results):
    """Converts Cozycozy API JSON response to a structured list of dictionaries."""
    if not results or 'entries' not in results:
        return []
    
    parsed_data = []
    for entry in results['entries']:
        base_info = {
            'id': entry.get('accommodationId'),
            'name': entry.get('name'),
            'title': entry.get('title'),
            'city': entry.get('cityName'),
            'rating_score': entry.get('ratingScore') or 0,
            'rating_count': entry.get('ratingCount') or 0,
            'location_text': entry.get('locationText'),
            'distance_km': parse_distance(entry.get('locationText')),
            'latitude': entry.get('coordinates', {}).get('latitude'),
            'longitude': entry.get('coordinates', {}).get('longitude'),
            'instant_booking': entry.get('instantBooking', False),
        }
        
        highlighted = entry.get('highlightedResults', [])
        if highlighted:
            cheapest = min(highlighted, key=lambda x: x.get('eurPricePerNight', float('inf')))
            
            base_info.update({
                'price_per_night_eur': cheapest.get('eurPricePerNight'),
                'total_price': cheapest.get('totalPrice', {}).get('value'),
                'currency': cheapest.get('totalPrice', {}).get('currencyCode'),
                'provider': cheapest.get('providerName'),
                'booking_url': cheapest.get('deeplinkUrl'),
                'room_type': cheapest.get('text'),
            })
            
            thumbnails = entry.get('lightThumbnails', {})
            first_urls = thumbnails.get('firstUrls', [])
            base_info['image_url'] = first_urls[0] if first_urls else None
        
        if 'price_per_night_eur' in base_info:
            parsed_data.append(base_info)
            
    return parsed_data
