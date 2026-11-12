#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VitaSteps Universal Dynamic Route Planner
Bármilyen két tetszőleges magyarországi (vagy külföldi) cím között tervez
valós idejű geocodinggal (Photon/OSM) és nyílt hálózati útvonalkereséssel (OSRM).

Használat:
    python landing_predikalo1/companion/plan_any_route.py "Pomáz, HÉV-állomás" "2097 Pilisborosjenő Fürdő köz 1."
    python landing_predikalo1/companion/plan_any_route.py "Szeged, Dóm tér" "Debrecen, Nagytemplom"
    python landing_predikalo1/companion/plan_any_route.py "Budapest, Nyugati pályaudvar" "Dobogókő, kilátó"
"""

import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

def geocode(query: str):
    """Bármilyen szöveges címet felold valós GPS koordinátára nyílt OSM/Photon API-val."""
    url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(query)}&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "VitaStepsDynamicPlanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("features"):
                feat = data["features"][0]
                coords = feat["geometry"]["coordinates"] # [lon, lat]
                props = feat.get("properties", {})
                display_name = ", ".join(filter(None, [
                    props.get("name"),
                    props.get("street"),
                    props.get("city") or props.get("county"),
                    props.get("country")
                ])) or query
                return {
                    "lat": coords[1],
                    "lon": coords[0],
                    "name": display_name
                }
    except Exception as e:
        sys.stderr.write(f"Geocoding hiba '{query}': {e}\n")
    return None

def route_network(lon1, lat1, lon2, lat2, mode="driving"):
    """Valós úthálózaton számol útvonalat, kanyarokat, távot és menetidőt OSRM motorral."""
    url = f"https://router.project-osrm.org/route/v1/{mode}/{lon1},{lat1};{lon2},{lat2}?overview=false&steps=true"
    req = urllib.request.Request(url, headers={"User-Agent": "VitaStepsDynamicPlanner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("routes"):
                r = data["routes"][0]
                return {
                    "distance_km": round(r["distance"] / 1000.0, 2),
                    "duration_min": round(r["duration"] / 60.0),
                    "steps": r.get("legs", [{}])[0].get("steps", [])
                }
    except Exception as e:
        sys.stderr.write(f"OSRM hiba: {e}\n")
    return None

def main():
    if len(sys.argv) >= 3:
        origin_text = sys.argv[1]
        dest_text = sys.argv[2]
    else:
        origin_text = "Pomáz, HÉV-állomás"
        dest_text = "2097 Pilisborosjenő Fürdő köz 1."

    print("=" * 72)
    print(" 🧭 VITASTEPS DINAMIKUS ÚTVONALTERVEZŐ (100% VALÓS FORRÁS)")
    print("=" * 72)
    print(f"📍 Kiindulópont: \"{origin_text}\"")
    print(f"🎯 Célállomás:   \"{dest_text}\"")
    print("⏳ Címek lekérdezése és valós útvonal generálása...")
    print("-" * 72)

    orig = geocode(origin_text)
    dest = geocode(dest_text)

    if not orig:
        print(f"❌ Nem sikerült feloldani a kiindulópontot: '{origin_text}'")
        return
    if not dest:
        print(f"❌ Nem sikerült feloldani a célállomást: '{dest_text}'")
        return

    print(f"✅ Indulás: {orig['name']} ({orig['lat']:.5f}, {orig['lon']:.5f})")
    print(f"✅ Érkezés: {dest['name']} ({dest['lat']:.5f}, {dest['lon']:.5f})")
    print("-" * 72)

    route = route_network(orig["lon"], orig["lat"], dest["lon"], dest["lat"])
    if not route:
        print("❌ Nem sikerült hálózati útvonalat generálni.")
        return

    dist_km = route["distance_km"]
    dur_min = route["duration_min"]
    dep_time = datetime.now()
    arr_time = dep_time + timedelta(minutes=dur_min)

    print(f"🛣️ Tervezett leggyorsabb útvonal:")
    print(f"   • Hálózati távolság:   {dist_km} km")
    print(f"   • Menetidő:            {dur_min} perc ({dur_min // 60} óra {dur_min % 60} perc)")
    print(f"   • Indulási idő:        {dep_time.strftime('%H:%M')}")
    print(f"   • Érkezési idő:        {arr_time.strftime('%H:%M')}")
    print()
    print("🚗 Valós útszakaszok és utcák a két pont között:")
    seen = []
    for step in route.get("steps", []):
        sname = step.get("name")
        if sname and sname not in seen:
            seen.append(sname)
            sm = int(round(step.get("distance", 0)))
            print(f"   ➔ {sname} ({sm} m)")

    print("=" * 72)

if __name__ == "__main__":
    main()
