import requests
import json
import uuid

def test_api():
    url = "https://api.skypicker.com/umbrella/v2/graphql?featureName=SearchOneWayItinerariesQuery"
    
    # Payload from scraper.py
    payload = {
        "query": """
        query SearchOneWayItinerariesQuery(
          $search: SearchOnewayInput
          $filter: ItinerariesFilterInput
          $options: ItinerariesOptionsInput
        ) {
          onewayItineraries(search: $search, filter: $filter, options: $options) {
            __typename
            ... on Itineraries {
              metadata {
                itinerariesCount
              }
              itineraries {
                id
                price {
                  amount
                }
                provider {
                  name
                }
              }
            }
            ... on AppError {
              error: message
            }
          }
        }
        """,
        "variables": {
            "search": {
                "itinerary": {
                    "source": {"ids": ["city:budapest_hu"]},
                    "destination": {"ids": ["city:london_gb"]}
                },
                "passengers": {"adults": 1, "children": 0, "infants": 0}
            },
            "filter": {"transportTypes": ["FLIGHT"], "limit": 1},
            "options": {"currency": "eur", "locale": "en", "market": "en", "partner": "skypicker"}
        }
    }

    # Header próba dummy adatokkal
    headers_dummy = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("Testing without tokens...")
    try:
        r = requests.post(url, json=payload, headers=headers_dummy, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        if "data" in data and "onewayItineraries" in data["data"]:
             itineraries = data["data"]["onewayItineraries"].get("itineraries", [])
             if itineraries:
                 print(f"First flight price: {itineraries[0]['price']['amount']} EUR")
                 print(f"Provider: {itineraries[0]['provider']['name']}")
             else:
                 print("No itineraries found in list.")
        else:
             print(f"Unexpected response structure: {data.keys()}")
    except Exception as e:
        print(f"Error: {e}")

    # Header próba generált UUID-vel
    headers_generated = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "kw-skypicker-visitor-uniqid": str(uuid.uuid4()),
        "kw-x-rand-id": str(uuid.uuid4())
        # umbrella token is the hard one
    }
    
    print("\nTesting with generated UUIDs (no umbrella)...")
    try:
        r = requests.post(url, json=payload, headers=headers_generated, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
