from selenium import webdriver
import json
import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List
from itertools import product

def get_kiwi_tokens(headless: bool = False) -> dict:
    """
    Kiwi.com tokenek megszerzése Selenium segítségével.
    
    Args:
        headless: Ha True, háttérben fut a böngésző
        
    Returns:
        Dictionary a tokenekkel: umbrella_token, visitor_id, rand_id
    """
    print("🚀 Tokenek megszerzése...")
    
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
    
    # FONTOS: Performance logging engedélyezése
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    # Egyszerű one-way keresés a tokenekhez
    url = "https://www.kiwi.com/hu/search/results/budapest-magyarorszag/barcelona-spanyolorszag/anytime/no-return/"
    driver.get(url)
    
    print("⏳ Várakozás a GraphQL hívásokra...")
    time.sleep(12)
    
    logs = driver.get_log("performance")
    
    umbrella_token = None
    visitor_id = None
    rand_id = None
    
    for entry in logs:
        message = json.loads(entry["message"])["message"]
        
        if (
            message["method"] == "Network.requestWillBeSent"
            and "graphql" in message["params"]["request"]["url"]
        ):
            headers = message["params"]["request"]["headers"]
            
            umbrella_token = headers.get("kw-umbrella-token")
            visitor_id = headers.get("kw-skypicker-visitor-uniqid")
            rand_id = headers.get("kw-x-rand-id")
            
            if umbrella_token:
                break
    
    driver.quit()
    
    print("✅ Tokenek megszerzve\n")
    
    return {
        "umbrella_token": umbrella_token,
        "visitor_id": visitor_id,
        "rand_id": rand_id
    }

def search_one_way_flights(
    origin: str,
    destination: str,
    tokens: dict,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    limit: int = 100,
    currency: str = "huf",
    locale: str = "hu",
    max_stopovers: Optional[int] = None,
    direct_flights_only: bool = False,
    debug: bool = False
) -> pd.DataFrame:
    """
    Kiwi.com egyirányú járatok keresése.
    """
    print(f"🔍 Egyirányú járatok: {origin} → {destination}", end="")
    if date_from and date_to:
        print(f" ({date_from} - {date_to})")
    elif date_from:
        print(f" (from {date_from})")
    elif date_to:
        print(f" (until {date_to})")
    else:
        print(" (anytime)")
    
    # City ID formázás
    if ":" not in origin:
        # ÚJ: Próbáljuk meg URL formátumból City ID-vé alakítani
        if "-" in origin:  # URL formátum (pl. "budapest-magyarorszag")
            origin_id = f"City:{origin.replace('-', '_')}"
            if debug:
                print(f"🔧 Origin URL->ID konverzió: {origin} -> {origin_id}")
        else:
            origin_id = f"City:{origin.lower()}"
    else:
        origin_id = origin
        
    if ":" not in destination:
        if "-" in destination:
            dest_id = f"City:{destination.replace('-', '_')}"
            if debug:
                print(f"🔧 Destination URL->ID konverzió: {destination} -> {dest_id}")
        else:
            dest_id = f"City:{destination.lower()}"
    else:
        dest_id = destination
    
    if debug:
        print(f"🔧 Végleges ID-k: {origin_id} -> {dest_id}")
    
    # GraphQL query - ONE WAY verzió
    graphql_payload = {
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
                __typename
                ... on ItineraryOneWay {
                  id
                  shareId
                  price {
                    amount
                  }
                  priceEur {
                    amount
                  }
                  provider {
                    name
                    code
                  }
                  sector {
                    id
                    duration
                    sectorSegments {
                      segment {
                        id
                        source {
                          localTime
                          utcTimeIso
                          station {
                            code
                            name
                            city {
                              name
                            }
                            country {
                              code
                            }
                          }
                        }
                        destination {
                          localTime
                          utcTimeIso
                          station {
                            code
                            name
                            city {
                              name
                            }
                            country {
                              code
                            }
                          }
                        }
                        carrier {
                          name
                          code
                        }
                        operatingCarrier {
                          name
                          code
                        }
                        duration
                        code
                      }
                      layover {
                        duration
                      }
                    }
                  }
                  bookingOptions {
                    edges {
                      node {
                        bookingUrl
                        price {
                          amount
                        }
                      }
                    }
                  }
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
                    "source": {"ids": [origin_id]},
                    "destination": {"ids": [dest_id]}
                },
                "passengers": {
                    "adults": adults,
                    "children": children,
                    "infants": infants
                }
            },
            "filter": {
                "transportTypes": ["FLIGHT"],
                "limit": limit
            },
            "options": {
                "currency": currency,
                "locale": locale,
                "market": locale,
                "partner": "skypicker"
            }
        }
    }
    
    # Dátumok hozzáadása
    if date_from or date_to:
        departure_date = {}
        if date_from:
            departure_date["start"] = f"{date_from}T00:00:00"
        if date_to:
            departure_date["end"] = f"{date_to}T23:59:59"
        graphql_payload["variables"]["search"]["itinerary"]["outboundDepartureDate"] = departure_date
        if debug:
            print(f"🔧 Dátum intervallum: {departure_date}")
    
    # Átszállások szűrése
    if direct_flights_only:
        graphql_payload["variables"]["filter"]["maxStopovers"] = 0
    elif max_stopovers is not None:
        graphql_payload["variables"]["filter"]["maxStopovers"] = max_stopovers
    
    if debug:
        print(f"🔧 Request payload:")
        print(json.dumps(graphql_payload["variables"], indent=2, ensure_ascii=False))
    
    # API hívás
    headers = {
        "Content-Type": "application/json",
        "kw-umbrella-token": tokens["umbrella_token"],
        "kw-skypicker-visitor-uniqid": tokens["visitor_id"],
        "kw-x-rand-id": tokens["rand_id"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.post(
        "https://api.skypicker.com/umbrella/v2/graphql?featureName=SearchOneWayItinerariesQuery",
        json=graphql_payload,
        headers=headers,
        timeout=30
    )
    
    if debug:
        print(f"🔧 Response status: {response.status_code}")
    
    data = response.json()
    
    if debug:
        print(f"🔧 Response data keys: {data.keys()}")
        if "data" in data:
            print(f"🔧 Data.onewayItineraries type: {data['data'].get('onewayItineraries', {}).get('__typename')}")
    
    # Hibakezelés
    if "errors" in data:
        print("❌ GraphQL hibák:")
        for error in data["errors"]:
            print(f"  - {error['message']}")
            if debug and "extensions" in error:
                print(f"    Extensions: {error['extensions']}")
        return pd.DataFrame()
    
    if not data.get("data") or not data["data"].get("onewayItineraries"):
        print("❌ Nem érkezett adat")
        if debug:
            print(f"🔧 Teljes response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return pd.DataFrame()
    
    result = data["data"]["onewayItineraries"]
    
    if result["__typename"] != "Itineraries":
        print(f"❌ Hiba: {result.get('error', 'Ismeretlen hiba')}")
        if debug:
            print(f"🔧 Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return pd.DataFrame()
    
    itineraries = result.get("itineraries", [])
    metadata = result.get("metadata", {})
    
    if debug:
        print(f"🔧 Metadata itinerariesCount: {metadata.get('itinerariesCount', 'N/A')}")
        print(f"🔧 Actual itineraries length: {len(itineraries)}")
    
    print(f"✅ {len(itineraries)} járat\n")

    # DataFrame építése
    flights_data = []
    
    for flight in itineraries:
        if flight["__typename"] != "ItineraryOneWay":
            continue
        
        # Alapadatok
        price = float(flight["price"]["amount"])
        price_eur = float(flight["priceEur"]["amount"])
        
        # Sector (útvonal)
        sector = flight["sector"]
        segments = sector["sectorSegments"]
        first_seg = segments[0]["segment"]
        last_seg = segments[-1]["segment"]
        
        dep_airport = first_seg["source"]["station"]["code"]
        dep_city = first_seg["source"]["station"]["city"]["name"]
        dep_time = first_seg["source"]["localTime"]
        dep_utc = first_seg["source"]["utcTimeIso"]
        
        arr_airport = last_seg["destination"]["station"]["code"]
        arr_city = last_seg["destination"]["station"]["city"]["name"]
        arr_time = last_seg["destination"]["localTime"]
        arr_utc = last_seg["destination"]["utcTimeIso"]
        
        duration_hours = sector["duration"] / 3600
        stops = len(segments) - 1
        
        # Légitársaságok
        carriers = list(set([seg["segment"]["carrier"]["name"] for seg in segments]))
        carrier_codes = list(set([seg["segment"]["carrier"]["code"] for seg in segments]))
        
        # Booking URL
        booking_url = None
        if flight.get("bookingOptions") and flight["bookingOptions"]["edges"]:
            booking_url = flight["bookingOptions"]["edges"][0]["node"].get("bookingUrl")
        
        flights_data.append({
            "id": flight["id"],
            "origin": origin,
            "destination": destination,
            "dep_city": dep_city,
            "dep_airport": dep_airport,
            "dep_time": dep_time,
            "dep_utc": dep_utc,
            "arr_city": arr_city,
            "arr_airport": arr_airport,
            "arr_time": arr_time,
            "arr_utc": arr_utc,
            "duration_h": round(duration_hours, 1),
            "stops": stops,
            "carriers": ", ".join(carriers),
            "carrier_codes": ", ".join(carrier_codes),
            "price_huf": price,
            "price_eur": price_eur,
            "provider": flight["provider"]["name"],
            "booking_url": booking_url
        })
    
    df = pd.DataFrame(flights_data)
    
    if not df.empty:
        # Dátum oszlopok konvertálása
        df["dep_time"] = pd.to_datetime(df["dep_time"])
        df["arr_time"] = pd.to_datetime(df["arr_time"])
        df["dep_utc"] = pd.to_datetime(df["dep_utc"])
        df["arr_utc"] = pd.to_datetime(df["arr_utc"])
        
        # Rendezés ár szerint
        df = df.sort_values("price_huf").reset_index(drop=True)
    
    return df

def create_return_combinations(
    outbound_df: pd.DataFrame,
    inbound_df: pd.DataFrame,
    min_stay_days: int = 2,
    max_stay_days: Optional[int] = None
) -> pd.DataFrame:
    """
    Oda-vissza kombinációk generálása két egyirányú DataFrame-ből.
    
    Args:
        outbound_df: Oda járatok DataFrame
        inbound_df: Vissza járatok DataFrame
        min_stay_days: Min tartózkodás napokban
        max_stay_days: Max tartózkodás napokban (None = korlátlan)
        
    Returns:
        DataFrame a visszajárat kombinációkkal
    """
    print(f"\n🔄 Kombinációk generálása...")
    print(f"   Oda járatok: {len(outbound_df)}")
    print(f"   Vissza járatok: {len(inbound_df)}")
    
    combinations = []
    
    for _, out_flight in outbound_df.iterrows():
        for _, in_flight in inbound_df.iterrows():
            # Ellenőrzés: visszaút később van-e mint odaút
            stay_days = (in_flight["dep_time"] - out_flight["arr_time"]).days
            
            if stay_days < min_stay_days:
                continue
            
            if max_stay_days and stay_days > max_stay_days:
                continue
            
            total_price_huf = out_flight["price_huf"] + in_flight["price_huf"]
            total_price_eur = out_flight["price_eur"] + in_flight["price_eur"]
            
            combinations.append({
                # Outbound
                "out_id": out_flight["id"],
                "out_dep_city": out_flight["dep_city"],
                "out_dep_airport": out_flight["dep_airport"],
                "out_dep_time": out_flight["dep_time"],
                "out_arr_city": out_flight["arr_city"],
                "out_arr_airport": out_flight["arr_airport"],
                "out_arr_time": out_flight["arr_time"],
                "out_duration_h": out_flight["duration_h"],
                "out_stops": out_flight["stops"],
                "out_carriers": out_flight["carriers"],
                "out_price_huf": out_flight["price_huf"],
                "out_booking_url": out_flight["booking_url"],
                
                # Inbound
                "in_id": in_flight["id"],
                "in_dep_city": in_flight["dep_city"],
                "in_dep_airport": in_flight["dep_airport"],
                "in_dep_time": in_flight["dep_time"],
                "in_arr_city": in_flight["arr_city"],
                "in_arr_airport": in_flight["arr_airport"],
                "in_arr_time": in_flight["arr_time"],
                "in_duration_h": in_flight["duration_h"],
                "in_stops": in_flight["stops"],
                "in_carriers": in_flight["carriers"],
                "in_price_huf": in_flight["price_huf"],
                "in_booking_url": in_flight["booking_url"],
                
                # Összesített
                "stay_days": stay_days,
                "total_price_huf": total_price_huf,
                "total_price_eur": total_price_eur,
                "total_stops": out_flight["stops"] + in_flight["stops"]
            })
    
    df = pd.DataFrame(combinations)
    
    if not df.empty:
        df = df.sort_values("total_price_huf").reset_index(drop=True)
        print(f"✅ {len(df)} érvényes kombináció\n")
    else:
        print("❌ Nincs érvényes kombináció\n")
    
    return df

def get_city_id_api(city_name: str) -> Optional[str]:
    """Kiwi API használata város ID lekéréséhez Selenium helyett."""
    url = f"https://api.skypicker.com/locations?term={city_name}&location_types=city"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('locations'):
            return data['locations'][0]['id']
    except Exception as e:
        print(f"❌ API hiba a városkeresésnél ({city_name}): {e}")
    return None

def search_flights_by_city_name_v2(
    origin_name: str,
    destination_name: str,
    tokens: dict,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    limit: int = 100,
    currency: str = "huf",
    locale: str = "hu",
    max_stopovers: Optional[int] = None,
    direct_flights_only: bool = False,
    headless: bool = True,
    debug: bool = False
) -> pd.DataFrame:
    """
    Járatok keresése város nevek alapján - JAVÍTOTT VERZIÓ.
    """
    origin_city_id = get_city_id_api(origin_name)
    if not origin_city_id:
        print(f"❌ Nem sikerült megszerezni az origin ID-t: {origin_name}")
        return pd.DataFrame()
    
    dest_city_id = get_city_id_api(destination_name)
    if not dest_city_id:
        print(f"❌ Nem sikerült megszerezni a destination ID-t: {destination_name}")
        return pd.DataFrame()
    
    
    if not origin_city_id or not dest_city_id:
        print(f"❌ Nem sikerült megszerezni a City ID-kat")
        return pd.DataFrame()
    
    # 3. Eredeti keresés a helyes City ID-kkel
    return search_one_way_flights(
        origin=origin_city_id,
        destination=dest_city_id,
        tokens=tokens,
        date_from=date_from,
        date_to=date_to,
        adults=adults,
        children=children,
        infants=infants,
        limit=limit,
        currency=currency,
        locale=locale,
        max_stopovers=max_stopovers,
        direct_flights_only=direct_flights_only,
        debug=debug
    )
