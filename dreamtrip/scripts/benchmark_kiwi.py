import asyncio
import time
import requests
import json
import pandas as pd
from scraper import get_kiwi_tokens, search_flights_by_city_name_v2, _perform_single_search, get_city_id_api
import concurrent.futures

# Sample cities to test with
CITIES = ["Paris", "Lisbon", "Bangkok", "Sydney", "Rome", "Barcelona", "Dubai", "New York", "Tokyo", "London"]

def benchmark_sequential():
    print(f"\n--- BENCHMARK: Sequential ({len(CITIES)} cities) ---")
    tokens = get_kiwi_tokens()
    start_time = time.time()
    results = []
    
    for city in CITIES:
        print(f"Fetching {city}...")
        df = search_flights_by_city_name_v2(
            "Budapest", city, tokens, 
            date_from="2026-06-10", date_to="2026-06-15", limit=1
        )
        results.append(len(df))
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Sequential Duration: {duration:.2f} seconds")
    return duration

def benchmark_parallel():
    print(f"\n--- BENCHMARK: Parallel Threaded ({len(CITIES)} cities) ---")
    tokens = get_kiwi_tokens()
    start_time = time.time()
    
    def fetch_city(city):
        return search_flights_by_city_name_v2(
            "Budapest", city, tokens, 
            date_from="2026-06-10", date_to="2026-06-15", limit=1
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(fetch_city, CITIES))
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Parallel Duration: {duration:.2f} seconds")
    return duration

def benchmark_batch():
    print(f"\n--- BENCHMARK: Batch (GraphQL Multi-ID) ---")
    tokens = get_kiwi_tokens()
    start_time = time.time()
    
    # Get all City IDs
    city_ids = []
    # Use simpler retrieval for benchmark speed
    for city in CITIES:
        if city == "Paris": city_ids.append("city:paris_fr")
        elif city == "Lisbon": city_ids.append("city:lisbon_pt")
        elif city == "Bangkok": city_ids.append("city:bangkok_th")
        elif city == "Sydney": city_ids.append("city:sydney_ns_au")
        elif city == "Rome": city_ids.append("city:rome_it")
        elif city == "Barcelona": city_ids.append("city:barcelona_es")
        elif city == "Dubai": city_ids.append("city:dubai_ae")
        elif city == "New York": city_ids.append("city:new_york_city_ny_us")
        elif city == "Tokyo": city_ids.append("city:tokyo_jp")
        elif city == "London": city_ids.append("city:london_gb")
    
    print(f"Batching {len(city_ids)} city IDs...")
    
    graphql_payload = {
        "query": """
        query SearchOneWayItinerariesQuery($search: SearchOnewayInput, $filter: ItinerariesFilterInput, $options: ItinerariesOptionsInput) {
          onewayItineraries(search: $search, filter: $filter, options: $options) {
            __typename
            ... on Itineraries {
              itineraries {
                ... on ItineraryOneWay {
                  price { amount }
                  sector {
                    sectorSegments {
                      segment {
                        destination { station { city { name id } } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """,
        "variables": {
            "search": {
                "itinerary": {
                    "source": {"ids": ["city:budapest_hu"]},
                    "destination": {"ids": city_ids},
                    "outboundDepartureDate": {"start": "2026-06-10T00:00:00", "end": "2026-06-20T23:59:59"}
                },
                "passengers": {"adults": 1, "children": 0, "infants": 0}
            },
            "filter": {"transportTypes": ["FLIGHT"], "limit": 200},
            "options": {"currency": "HUF", "locale": "hu", "market": "hu", "partner": "skypicker"}
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.post("https://api.skypicker.com/umbrella/v2/graphql", json=graphql_payload, headers=headers)
    data = response.json()
    
    itits_data = data.get("data", {}).get("onewayItineraries", {})
    itineraries = itits_data.get("itineraries", []) if isinstance(itits_data, dict) else []
    
    print(f"Found {len(itineraries)} itineraries in one call.")
    
    cheapest = {}
    for flight in itineraries:
        try:
            city_name = flight["sector"]["sectorSegments"][-1]["segment"]["destination"]["station"]["city"]["name"]
            price = float(flight["price"]["amount"])
            if city_name not in cheapest or price < cheapest[city_name]:
                cheapest[city_name] = price
        except: continue
            
    print(f"Cities with results: {list(cheapest.keys())}")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Batch Duration: {duration:.2f} seconds")
    return duration

if __name__ == "__main__":
    s_dur = benchmark_sequential()
    p_dur = benchmark_parallel()
    b_dur = benchmark_batch()
    
    print("\n" + "="*30)
    print("FINAL COMPARISON")
    print(f"Sequential: {s_dur:.2f}s")
    print(f"Parallel:   {p_dur:.2f}s")
    print(f"Batch:      {b_dur:.2f}s")
    print("="*30)
