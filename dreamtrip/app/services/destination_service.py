import os
import json
from typing import List, Dict, Any, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "destinations.json")

def load_all_destinations() -> List[Dict[str, Any]]:
    """Betölti a célállomások tiszta listáját a destinations.json fájlból."""
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_filtered_destinations(exclusions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Kiszűri a célállomásokat a kizárt régiók vagy országok alapján.
    Pl. exclusions: ['region_asia', 'region_america']
    """
    all_dests = load_all_destinations()
    if not exclusions:
        return all_dests

    filtered = []
    for d in all_dests:
        region = d.get("region", "").lower()
        # Ellenőrizzük a kizárási kulcsokat
        is_excluded = False
        for exc in exclusions:
            exc_clean = exc.replace("region_", "").lower()
            if exc_clean in region:
                is_excluded = True
                break
        if not is_excluded:
            filtered.append(d)
            
    return filtered

def find_destination_by_city(city_name: str) -> Optional[Dict[str, Any]]:
    """Megkeres egy célállomást a név vagy város alapján."""
    dests = load_all_destinations()
    c_lower = city_name.lower().strip()
    for d in dests:
        if d.get("city", "").lower() == c_lower or d.get("name", "").lower() == c_lower:
            return d
    return None
