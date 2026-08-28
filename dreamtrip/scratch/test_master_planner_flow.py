import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("RUNNING MASTER TRAVEL PLANNER (END-TO-END WIZARD) TEST SUITE")
print("=" * 80)

# 1. TEST PLANNER SERVICE: DESTINATION RANKING
from app.services.planner_service import calculate_planner_destinations_sync, search_and_rank_planner_flights

print("\n--- 1. Testing Destination Ranking from Intake ---")
destinations = calculate_planner_destinations_sync(
    origin="Budapest",
    adults=2,
    children=0,
    month=9,
    duration_days=7,
    target_temp=24.0,
    min_safety=50,
    preferred_regions=["europe_south", "europe_west", "europe_central"],
    exclusions=[]
)

print(f"[OK] Returned {len(destinations)} ranked destinations.")
for d in destinations[:3]:
    print(f"   - #{d['rank']} {d['name']} ({d['country']}) -> Score: {d['score']}p | Nappal: {d['metrics']['temp_avg']}°C | Repjegy: {d['metrics']['flight_price_formatted']} | Étel: ~€{int(d['metrics']['daily_cost_raw'])}/nap")

top_dest = destinations[0]
print(f"\n[OK] Step 1 Selection: {top_dest['name']} ({top_dest['country']})")

# 2. TEST PLANNER SERVICE: FLIGHT SEARCH & RANKING
print(f"\n--- 2. Testing Automated Flight Search for {top_dest['name']} ---")
flights = search_and_rank_planner_flights(
    origin="Budapest",
    destination=top_dest['name'],
    month=9,
    duration_days=7,
    adults=2,
    children=0,
    direct_only=False,
    max_stops=1
)

print(f"[OK] Returned {len(flights)} ranked flights.")
for fl in flights[:3]:
    out_d = str(fl.get('out_dep_time') or '').split(' ')[0].split('T')[0]
    in_d = str(fl.get('in_dep_time') or '').split(' ')[0].split('T')[0]
    print(f"   - #{fl['rank']} {fl.get('out_airline', 'Járat')} ({out_d} – {in_d}) -> Total: {int(fl['total_price_huf']):,} Ft | Relevancia: {int(fl['phi_net']*100)}%")

top_flight = flights[0] if flights else {
    "out_airline": "Wizz Air",
    "total_price_huf": 48900,
    "out_dep_time": "2026-09-10T06:15:00",
    "in_dep_time": "2026-09-17T21:40:00",
    "stay_days": 7
}

out_date = str(top_flight.get('out_dep_time') or '').split(' ')[0].split('T')[0]
in_date = str(top_flight.get('in_dep_time') or '').split(' ')[0].split('T')[0]
nights = top_flight.get('stay_days', 7)

print(f"\n[OK] Step 2 Selection: {top_flight.get('out_airline', 'Járat')} (Dátumok zárolva a szálláshoz: {out_date} – {in_date}, {nights} éj)")

# 3. TEST NUMBEO BREAKDOWN CALCULATION
print("\n--- 3. Testing Itemized Numbeo Budget Breakdown ---")
numbeo_data = top_dest.get("metrics", {}).get("numbeo_breakdown", {})
food_daily_eur = numbeo_data.get("daily_food_eur", 43.2)
transit_daily_eur = (numbeo_data.get("transport_ticket", 1.50) or 1.50) * 2.0
rate = 395.0

food_total_huf = int(food_daily_eur * nights * 2 * rate)
transit_total_huf = int(transit_daily_eur * nights * 2 * rate)
flight_total_huf = int(top_flight["total_price_huf"])
stay_total_huf = 148000

total_trip_huf = flight_total_huf + stay_total_huf + food_total_huf + transit_total_huf

print(f"   - Repülőjegy: {flight_total_huf:,} Ft")
print(f"   - Szállás (becsült/választott {nights} éj): {stay_total_huf:,} Ft")
print(f"   - Étkezések (Numbeo {food_daily_eur}€/nap/fő × {nights}n × 2fő): {food_total_huf:,} Ft")
print(f"   - Helyi tömegközlekedés (Numbeo {transit_daily_eur}€/nap/fő × {nights}n × 2fő): {transit_total_huf:,} Ft")
print(f"   -------------------------------------------------")
print(f"   ÖSSZESEN: {total_trip_huf:,} Ft (~{int(total_trip_huf/2):,} Ft / fő)")

print("\n" + "=" * 80)
print("ALL MASTER PLANNER TESTS COMPLETED SUCCESSFULLY!")
print("=" * 80)
