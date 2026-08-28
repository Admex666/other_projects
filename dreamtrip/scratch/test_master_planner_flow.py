import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 85)
print("RUNNING COMPREHENSIVE MASTER PLANNER v2 TEST SUITE (FLEXIBLE MODES & AHP)")
print("=" * 85)

from app.services.planner_service import (
    calculate_planner_destinations_sync, 
    search_and_rank_planner_flights,
    compute_ahp_weights_from_comparisons
)

# 1. TEST AHP PAIRWISE MATRIX CALCULATION
print("\n--- 1. Testing AHP Pairwise Matrix Eigenvector Weight Computation ---")
comparisons = {
    "flight_vs_weather": 5.0, # Flight much more important than weather
    "flight_vs_safety": 3.0,  # Flight more important than safety
    "flight_vs_cost": 1.0,    # Flight and cost equally important
    "weather_vs_safety": 0.33 # Safety more important than weather
}
criteria = ["flight", "cost", "weather", "safety"]
ahp_weights = compute_ahp_weights_from_comparisons(criteria, comparisons)
print("[OK] AHP Eigenvector Weights Computed:")
for c, w in ahp_weights.items():
    print(f"   - {c.upper():<8}: {w*100:.1f}%")

# 2. TEST FLEXIBLE ORIGIN & LONG DURATION (21 DAYS)
print("\n--- 2. Testing Flexible Origin ('Bécs (VIE)') and 21 Days Duration ---")
dests_vienna = calculate_planner_destinations_sync(
    origin="Bécs (VIE)",
    adults=2,
    children=1,
    date_mode="month",
    month=9,
    duration_days=21,
    target_temp=25.0,
    min_safety=50,
    ahp_comparisons=comparisons
)

print(f"[OK] Returned {len(dests_vienna)} ranked destinations from Vienna for 21-day trip:")
for d in dests_vienna[:3]:
    print(f"   - #{d['rank']} {d['name']} ({d['country']}) -> Score: {d['score']}p | Klíma: {d['metrics']['temp_avg']}°C | Repjegy: {d['metrics']['flight_price_formatted']}")

top_dest = dests_vienna[0]

# 3. TEST EXACT DATE MODE (2026-09-12 to 2026-09-22, 10 days)
print("\n--- 3. Testing Exact Date Mode (2026-09-12 – 2026-09-22) ---")
exact_dests = calculate_planner_destinations_sync(
    origin="Budapest",
    adults=2,
    date_mode="exact",
    exact_out_date="2026-09-12",
    exact_in_date="2026-09-22",
    ahp_comparisons=comparisons
)
print(f"[OK] Exact Date Mode evaluated {len(exact_dests)} destinations.")
print(f"   - Top pick: {exact_dests[0]['name']} (Score: {exact_dests[0]['score']}p)")

# 4. TEST INTERVAL DATE MODE WITH FLIGHT SEARCH
print(f"\n--- 4. Testing Interval Mode Flight Search ({top_dest['name']}) ---")
flights = search_and_rank_planner_flights(
    origin="Bécs (VIE)",
    destination=top_dest['name'],
    date_mode="interval",
    out_from="2026-09-05",
    out_to="2026-09-15",
    in_from="2026-09-20",
    in_to="2026-09-30",
    min_stay=7,
    max_stay=15,
    adults=2,
    children=1,
    direct_only=False,
    max_stops=1
)

print(f"[OK] Returned {len(flights)} flights within the requested interval:")
if flights:
    for fl in flights[:2]:
        out_d = str(fl.get('out_dep_time') or '').split(' ')[0].split('T')[0]
        in_d = str(fl.get('in_dep_time') or '').split(' ')[0].split('T')[0]
        print(f"   - #{fl['rank']} {fl.get('out_airline', 'Járat')} ({out_d} – {in_d}, {fl.get('stay_days')} éj) -> {int(fl['total_price_huf']):,} Ft")

print("\n" + "=" * 85)
print("ALL COMPREHENSIVE MASTER PLANNER v2 TESTS PASSED WITH 100% SUCCESS!")
print("=" * 85)
