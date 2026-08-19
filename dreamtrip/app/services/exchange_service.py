import time
import requests
from typing import Optional

_CACHED_EUR_HUF_RATE: Optional[float] = None
_LAST_FETCH_TIME: float = 0.0
CACHE_TTL_SECONDS: float = 3600.0  # 1 órás in-memory cache

def get_eur_huf_rate() -> float:
    """
    Lekéri a legfrissebb hivatalos EUR/HUF devizaárfolyamot 1 órás gyorsítótárazással.
    Elsődleges forrás: Európai Központi Bank (ECB) / Frankfurter API,
    Tartalék forrás: Open Exchange Rates API.
    """
    global _CACHED_EUR_HUF_RATE, _LAST_FETCH_TIME
    
    current_time = time.time()
    if _CACHED_EUR_HUF_RATE and (current_time - _LAST_FETCH_TIME < CACHE_TTL_SECONDS):
        return _CACHED_EUR_HUF_RATE

    # 1. Elsődleges: Frankfurter API (Hivatalos EKB napi árfolyam)
    try:
        res = requests.get('https://api.frankfurter.app/latest?from=EUR&to=HUF', timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            rate = float(data.get('rates', {}).get('HUF', 0))
            if rate > 200:
                _CACHED_EUR_HUF_RATE = round(rate, 2)
                _LAST_FETCH_TIME = current_time
                print(f"[INFO] Élő EUR/HUF árfolyam frissítve (EKB / Frankfurter): {_CACHED_EUR_HUF_RATE} Ft")
                return _CACHED_EUR_HUF_RATE
    except Exception as e:
        print(f"[WARN] Frankfurter árfolyam lekérés sikertelen ({e}), tartalék API hívása...")

    # 2. Másodlagos tartalék: Open ER-API
    try:
        res = requests.get('https://open.er-api.com/v6/latest/EUR', timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            rate = float(data.get('rates', {}).get('HUF', 0))
            if rate > 200:
                _CACHED_EUR_HUF_RATE = round(rate, 2)
                _LAST_FETCH_TIME = current_time
                print(f"[INFO] Élő EUR/HUF árfolyam frissítve (Open ER-API): {_CACHED_EUR_HUF_RATE} Ft")
                return _CACHED_EUR_HUF_RATE
    except Exception as e:
        print(f"[WARN] Open ER-API árfolyam lekérés sikertelen ({e})")

    # 3. Ha offline vagy hiba lépett fel, meglévő vagy biztonsági fallback
    if _CACHED_EUR_HUF_RATE:
        return _CACHED_EUR_HUF_RATE
    
    print("[WARN] Offline fallback árfolyam használata: 395.0 Ft")
    return 395.0
