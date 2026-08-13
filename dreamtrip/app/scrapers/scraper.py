# from selenium import webdriver
import json
import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List, Callable
from itertools import product

def get_kiwi_tokens(headless: bool = False) -> dict:
    """
    Kiwi.com tokenek (mockolt) megszerzése - Selenium NÉLKÜL.
    A modern API nem igényel szigorú token ellenőrzést, így a böngészős megoldás
    kiváltható egy egyszerű visszatéréssel. Ez drasztikusan csökkenti a memóriahasználatot.
    """
    print("[INFO] Tokenek optimalizált megszerzése (No-Selenium)...")
    return {
        "umbrella_token": None,
        "visitor_id": None,
        "rand_id": None
    }

from datetime import timedelta

def _perform_single_search(
    origin_id: str,
    dest_id: str,
    tokens: dict,
    date_from: Optional[str],
    date_to: Optional[str],
    adults: int,
    children: int,
    infants: int,
    limit: int,
    currency: str,
    locale: str,
    max_stopovers: Optional[int],
    direct_flights_only: bool,
    debug: bool
) -> List[dict]:
    """Belső segédfüggvény egyetlen API hívás végrehajtásához."""
    
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
            print(f"[DEBUG] Dátum intervallum: {departure_date}")
    
    # Átszállások szűrése
    if direct_flights_only:
        graphql_payload["variables"]["filter"]["maxStopovers"] = 0
    elif max_stopovers is not None:
        graphql_payload["variables"]["filter"]["maxStopovers"] = max_stopovers
    
    if debug:
        print(f"[DEBUG] Request payload: {json.dumps(graphql_payload['variables'], indent=2, ensure_ascii=False)}")
    
    # API hívás
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    if tokens.get("umbrella_token"):
        headers["kw-umbrella-token"] = tokens["umbrella_token"]
    if tokens.get("visitor_id"):
        headers["kw-skypicker-visitor-uniqid"] = tokens["visitor_id"]
    if tokens.get("rand_id"):
        headers["kw-x-rand-id"] = tokens["rand_id"]
    
    try:
        response = requests.post(
            "https://api.skypicker.com/umbrella/v2/graphql?featureName=SearchOneWayItinerariesQuery",
            json=graphql_payload,
            headers=headers,
            timeout=30
        )
        
        if debug:
            print(f"[DEBUG] Response status: {response.status_code}")
        
        data = response.json()
        
        if "errors" in data:
            print("[ERROR] GraphQL hibák:")
            for error in data["errors"]:
                print(f"  - {error['message']}")
            return []
        
        if not data.get("data") or not data["data"].get("onewayItineraries"):
            print("[ERROR] Nem érkezett adat")
            return []
        
        result = data["data"]["onewayItineraries"]
        
        if result["__typename"] != "Itineraries":
            print(f"[ERROR] Hiba: {result.get('error', 'Ismeretlen hiba')}")
            return []
        
        return result.get("itineraries", [])
        
    except Exception as e:
        print(f"[ERROR] Hiba a kérés során: {e}")
        return []

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
    debug: bool = False,
    progress_callback: Optional[Callable[[int], None]] = None
) -> pd.DataFrame:
    """
    Kiwi.com egyirányú járatok keresése.
    Automatikusan darabolja a keresést 5 napos intervallumokra, ha szükséges.
    """
    print(f"[INFO] Egyirányú járatok: {origin} -> {destination}", end="")
    if date_from and date_to:
        print(f" ({date_from} - {date_to})")
    else:
        print(" (anytime)")
    
    # City ID formázás
    if ":" not in origin:
        if "-" in origin:
            origin_id = f"City:{origin.replace('-', '_')}"
        else:
            origin_id = f"City:{origin.lower()}"
    else:
        origin_id = origin
        
    if ":" not in destination:
        if "-" in destination:
            dest_id = f"City:{destination.replace('-', '_')}"
        else:
            dest_id = f"City:{destination.lower()}"
    else:
        dest_id = destination
    
    # Dátum logika feldolgozása
    search_intervals = []
    
    if date_from and date_to:
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        delta = (end - start).days
        
        # Ha a különbség nagyobb mint 5 nap, daraboljuk
        if delta > 5:
            print(f"[INFO] Nagy időintervallum ({delta} nap) -> Darabolás 5 napos csonkokra, limit=50/chunk")
            current = start
            while current <= end:
                chunk_end = min(current + timedelta(days=4), end)
                search_intervals.append({
                    "from": current.strftime("%Y-%m-%d"),
                    "to": chunk_end.strftime("%Y-%m-%d"),
                    "limit": 50 # Fix 50-es limit chunkonként
                })
                current = chunk_end + timedelta(days=1)
        else:
            search_intervals.append({
                "from": date_from,
                "to": date_to,
                "limit": limit
            })
    else:
        # Ha nincs dátum megadva, vagy csak egyik, marad az eredeti logikánál
        search_intervals.append({
            "from": date_from,
            "to": date_to,
            "limit": limit
        })

    all_itineraries = []
    total_intervals = len(search_intervals)
    
    for idx, interval in enumerate(search_intervals):
        if progress_callback:
            percent = int((idx / total_intervals) * 100)
            progress_callback(percent)

        print(f"   -> Keresés: {interval['from']} - {interval['to']} (Limit: {interval['limit']})")
        
        itineraries = _perform_single_search(
            origin_id=origin_id,
            dest_id=dest_id,
            tokens=tokens,
            date_from=interval['from'],
            date_to=interval['to'],
            adults=adults,
            children=children,
            infants=infants,
            limit=interval['limit'],
            currency=currency,
            locale=locale,
            max_stopovers=max_stopovers,
            direct_flights_only=direct_flights_only,
            debug=debug
        )
        all_itineraries.extend(itineraries)
        time.sleep(1) # Kis pihenő a kérések között
        
    print(f"[INFO] Összesen {len(all_itineraries)} járat találva\n")

    # DataFrame építése
    flights_data = []
    
    for flight in all_itineraries:
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
        
        # Dublikátumok szűrése (ha lenne átfedés)
        df = df.drop_duplicates(subset=["id"])
        
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
    print(f"\n[INFO] Kombinációk generálása...")
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
        print(f"[INFO] {len(df)} érvényes kombináció\n")
    else:
        print("[INFO] Nincs érvényes kombináció\n")
    
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
        print(f"[ERROR] API hiba a városkeresésnél ({city_name}): {e}")
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
    debug: bool = False,
    progress_callback: Optional[Callable[[int], None]] = None
) -> pd.DataFrame:
    """
    Járatok keresése város nevek alapján - JAVÍTOTT VERZIÓ.
    """
    origin_city_id = get_city_id_api(origin_name)
    if not origin_city_id:
        print(f"[ERROR] Nem sikerült megszerezni az origin ID-t: {origin_name}")
        return pd.DataFrame()
    
    dest_city_id = get_city_id_api(destination_name)
    if not dest_city_id:
        print(f"[ERROR] Nem sikerült megszerezni a destination ID-t: {destination_name}")
        return pd.DataFrame()
    
    
    if not origin_city_id or not dest_city_id:
        print(f"[ERROR] Nem sikerült megszerezni a City ID-kat")
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
        debug=debug,
        progress_callback=progress_callback
    )
