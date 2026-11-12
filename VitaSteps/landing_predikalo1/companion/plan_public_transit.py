"""
Universal Public Transit & Hiking Route Planner
Uses OpenStreetMap Nominatim/Photon Geocoding, Real GTFS timetable data (BKK + Volánbusz),
DATE-AWARE scheduling (calendar_dates: weekdays, saturdays, sundays, holidays),
and strict physical walking transfers between stops (max 850m with walk time calculated).
"""

import sys
import json
import math
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta

DB_PATH = 'landing_predikalo1/companion/otp/transit.db'
MAX_TRANSFER_WALK_METERS = 850  # Szigorú maximális átszállási gyaloglási távolság (pl. Szentlélek tér H -> Flórián tér)
WALKING_SPEED_KMH = 4.5         # Átlagos gyaloglási sebesség (km/h)

def parse_target_date(date_str=None):
    """
    Parse date input string into (formatted_date_str 'YYYYMMDD', readable_str, day_of_week_hu).
    Supports:
      - None or 'ma' -> Today
      - 'holnap' -> Tomorrow
      - 'szombat' -> Nearest upcoming Saturday
      - 'vasarnap' / 'vasárnap' -> Nearest upcoming Sunday
      - 'YYYY-MM-DD' or 'YYYYMMDD'
    """
    today = date.today()
    hu_days = {
        0: 'hétfő', 1: 'kedd', 2: 'szerda', 3: 'csütörtök',
        4: 'péntek', 5: 'szombat', 6: 'vasárnap'
    }

    if not date_str or date_str.lower() in ('ma', 'today'):
        target = today
    elif date_str.lower() in ('holnap', 'tomorrow'):
        target = today + timedelta(days=1)
    elif date_str.lower() in ('szombat', 'saturday'):
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0 and datetime.now().hour >= 18:
            days_ahead = 7
        target = today + timedelta(days=days_ahead)
    elif date_str.lower() in ('vasarnap', 'vasárnap', 'sunday'):
        days_ahead = (6 - today.weekday()) % 7
        if days_ahead == 0 and datetime.now().hour >= 18:
            days_ahead = 7
        target = today + timedelta(days=days_ahead)
    else:
        # Try parse YYYY-MM-DD or YYYYMMDD
        clean = date_str.replace('-', '').replace('.', '').replace('/', '').strip()
        try:
            target = datetime.strptime(clean, "%Y%m%d").date()
        except Exception:
            target = today

    gtfs_date = target.strftime("%Y%m%d")
    readable = target.strftime("%Y.%m.%d")
    day_name = hu_days[target.weekday()]
    return gtfs_date, readable, day_name

def geocode_address(address_str):
    """Geocode any Hungarian address to (lat, lon, display_name)."""
    # 1. Try Photon (Komoot OSM geocoder)
    try:
        url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(address_str)}&limit=3&lang=hu"
        req = urllib.request.Request(url, headers={'User-Agent': 'VitaStepsHiking/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('features'):
                f = data['features'][0]
                lon, lat = f['geometry']['coordinates']
                props = f.get('properties', {})
                name = props.get('name') or props.get('street') or address_str
                city = props.get('city') or props.get('district') or ''
                display = f"{name}, {city}".strip(', ')
                return lat, lon, display
    except Exception:
        pass

    # 2. Try Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(address_str)}&format=json&limit=1&countrycodes=hu"
        req = urllib.request.Request(url, headers={'User-Agent': 'VitaStepsHiking/1.0 (adam@vitasteps.hu)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data:
                return float(data[0]['lat']), float(data[0]['lon']), data[0]['display_name']
    except Exception as e:
        print(f"Geocoding error: {e}", file=sys.stderr)

    return None, None, None

def get_walking_metrics(lat1, lon1, lat2, lon2):
    """Calculate realistic pedestrian walking distance (meters/km) and duration (minutes)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    crow_km = R * c
    walk_km = crow_km * 1.25
    walk_m = walk_km * 1000.0
    walk_min = (walk_km / WALKING_SPEED_KMH) * 60.0
    return walk_km, walk_m, walk_min

def find_nearest_stops(conn, lat, lon, max_dist_km=2.0, limit=8):
    """Find active transit stops within max_dist_km of an address."""
    cur = conn.cursor()
    lat_deg = max_dist_km / 111.0
    lon_deg = max_dist_km / 75.0

    cur.execute('''
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops
        WHERE is_active = 1
          AND stop_lat BETWEEN ? AND ?
          AND stop_lon BETWEEN ? AND ?
    ''', (lat - lat_deg, lat + lat_deg, lon - lon_deg, lon + lon_deg))

    results = []
    for sid, name, slat, slon in cur.fetchall():
        w_km, w_m, w_min = get_walking_metrics(lat, lon, slat, slon)
        if w_km <= max_dist_km:
            results.append({
                'stop_id': sid,
                'stop_name': name,
                'lat': slat,
                'lon': slon,
                'walk_dist_km': w_km,
                'walk_m': w_m,
                'walk_min': w_min
            })

    results.sort(key=lambda x: x['walk_min'])
    return results[:limit]

def find_direct_connections(conn, origin_stops, dest_stops, earliest_time_str, gtfs_date):
    """Find direct transit trips operating on `gtfs_date`."""
    cur = conn.cursor()
    orig_ids = [s['stop_id'] for s in origin_stops]
    dest_ids = [s['stop_id'] for s in dest_stops]

    if not orig_ids or not dest_ids:
        return []

    orig_map = {s['stop_id']: s for s in origin_stops}
    dest_map = {s['stop_id']: s for s in dest_stops}

    orig_placeholders = ','.join(['?'] * len(orig_ids))
    dest_placeholders = ','.join(['?'] * len(dest_ids))

    query = f'''
        SELECT st1.trip_id, r.route_short_name, r.route_long_name, t.trip_headsign,
               st1.stop_id, st1.departure_time, st2.stop_id, st2.arrival_time
        FROM stop_times st1
        JOIN stop_times st2 ON st1.trip_id = st2.trip_id
        JOIN trips t ON st1.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        JOIN calendar_dates cd ON t.service_id = cd.service_id
        WHERE st1.stop_id IN ({orig_placeholders})
          AND st2.stop_id IN ({dest_placeholders})
          AND st1.stop_sequence < st2.stop_sequence
          AND cd.date = ?
          AND cd.exception_type = 1
          AND st1.departure_time >= ?
        ORDER BY st2.arrival_time ASC
        LIMIT 5
    '''
    params = orig_ids + dest_ids + [gtfs_date, earliest_time_str]
    cur.execute(query, params)

    routes = []
    for tid, r_short, r_long, headsign, o_sid, dep, d_sid, arr in cur.fetchall():
        routes.append({
            'type': 'direct',
            'trip_id': tid,
            'route_short': r_short,
            'route_long': r_long,
            'headsign': headsign,
            'orig_stop': orig_map[o_sid],
            'dest_stop': dest_map[d_sid],
            'dep_time': dep,
            'arr_time': arr
        })
    return routes

def find_strict_transfer_connections(conn, origin_stops, dest_stops, earliest_time_str, gtfs_date):
    """
    Find 1-transfer connections active on `gtfs_date` with STRICT physical transfer walk limits:
    The walk between transfer stops MUST be <= MAX_TRANSFER_WALK_METERS (850m).
    The walk time is explicitly added to the departure requirement of the second leg!
    """
    cur = conn.cursor()
    dest_ids = [s['stop_id'] for s in dest_stops]
    dest_map = {s['stop_id']: s for s in dest_stops}

    candidates = []

    for o in origin_stops[:3]:
        cur.execute('''
            SELECT st1.trip_id, r1.route_short_name, t1.trip_headsign, st1.departure_time,
                   st2.stop_id, s2.stop_name, s2.stop_lat, s2.stop_lon, st2.arrival_time
            FROM stop_times st1
            JOIN stop_times st2 ON st1.trip_id = st2.trip_id
            JOIN trips t1 ON st1.trip_id = t1.trip_id
            JOIN routes r1 ON t1.route_id = r1.route_id
            JOIN stops s2 ON st2.stop_id = s2.stop_id
            JOIN calendar_dates cd1 ON t1.service_id = cd1.service_id
            WHERE st1.stop_id = ?
              AND cd1.date = ?
              AND cd1.exception_type = 1
              AND st1.departure_time >= ?
              AND st1.stop_sequence < st2.stop_sequence
            ORDER BY st1.departure_time ASC
            LIMIT 40
        ''', (o['stop_id'], gtfs_date, earliest_time_str))

        first_legs = cur.fetchall()

        for t1_id, r1_short, t1_head, dep1, mid1_sid, mid1_name, mid1_lat, mid1_lon, arr1 in first_legs:
            arr1_h, arr1_m, arr1_s = map(int, arr1.split(':'))
            t1_arr_dt = timedelta(hours=arr1_h, minutes=arr1_m, seconds=arr1_s)

            # Find active stops near mid1 within MAX_TRANSFER_WALK_METERS (850m)
            cur.execute('''
                SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
                FROM stops s
                WHERE s.is_active = 1
                  AND s.stop_lat BETWEEN ? AND ?
                  AND s.stop_lon BETWEEN ? AND ?
            ''', (mid1_lat - 0.008, mid1_lat + 0.008, mid1_lon - 0.012, mid1_lon + 0.012))

            nearby_mid_stops = cur.fetchall()

            for mid2_sid, mid2_name, mid2_lat, mid2_lon in nearby_mid_stops:
                w_km, w_m, w_min = get_walking_metrics(mid1_lat, mid1_lon, mid2_lat, mid2_lon)
                if w_m > MAX_TRANSFER_WALK_METERS:
                    continue

                min_dep2_dt = t1_arr_dt + timedelta(minutes=math.ceil(w_min) + 3)
                min_dep2_sec = int(min_dep2_dt.total_seconds())
                min_dep2_str = f"{min_dep2_sec//3600:02d}:{(min_dep2_sec%3600)//60:02d}:00"

                cur.execute(f'''
                    SELECT st3.trip_id, r2.route_short_name, t2.trip_headsign, st3.departure_time,
                           st4.stop_id, st4.arrival_time
                    FROM stop_times st3
                    JOIN stop_times st4 ON st3.trip_id = st4.trip_id
                    JOIN trips t2 ON st3.trip_id = t2.trip_id
                    JOIN routes r2 ON t2.route_id = r2.route_id
                    JOIN calendar_dates cd2 ON t2.service_id = cd2.service_id
                    WHERE st3.stop_id = ?
                      AND st4.stop_id IN ({','.join(['?']*len(dest_ids))})
                      AND cd2.date = ?
                      AND cd2.exception_type = 1
                      AND st3.stop_sequence < st4.stop_sequence
                      AND st3.departure_time >= ?
                      AND st3.departure_time <= time(?, '+45 minutes')
                    ORDER BY st4.arrival_time ASC
                    LIMIT 1
                ''', [mid2_sid] + dest_ids + [gtfs_date, min_dep2_str, min_dep2_str])

                leg2 = cur.fetchone()
                if leg2:
                    t2_id, r2_short, t2_head, dep2, d_sid, arr2 = leg2
                    candidates.append({
                        'type': 'transfer',
                        'leg1': {
                            'route_short': r1_short,
                            'headsign': t1_head,
                            'orig_stop': o,
                            'dep_time': dep1,
                            'dest_stop': mid1_name,
                            'arr_time': arr1
                        },
                        'transfer_walk': {
                            'dist_m': int(round(w_m)),
                            'walk_min': int(round(w_min)),
                            'from_stop': mid1_name,
                            'to_stop': mid2_name
                        },
                        'leg2': {
                            'route_short': r2_short,
                            'headsign': t2_head,
                            'orig_stop': mid2_name,
                            'dep_time': dep2,
                            'dest_stop': dest_map[d_sid],
                            'arr_time': arr2
                        },
                        'total_arr_time': arr2
                    })

    candidates.sort(key=lambda c: c['total_arr_time'])
    return candidates[:3]

def plan_journey(start_address, end_address, dep_time_str="08:00:00", date_input=None):
    gtfs_date, readable_date, day_name = parse_target_date(date_input)

    print(f"\n=======================================================")
    print(f"🗺️  VITASTEPS TÖMEGKÖZLEKEDÉSI ÚTVONALTERVEZŐ (BKK & VOLÁNBUSZ GTFS)")
    print(f"=======================================================")
    print(f"📍 Indulás: {start_address}")
    print(f"🏁 Érkezés: {end_address}")
    print(f"📅 Tervezés napja: {readable_date} ({day_name})")
    print(f"⏰ Kívánt indulási idő: {dep_time_str}")
    print(f"🚶 Max. átszállási körzet: {MAX_TRANSFER_WALK_METERS} m\n")

    # 1. Geocode
    s_lat, s_lon, s_disp = geocode_address(start_address)
    if not s_lat:
        print(f"❌ Nem sikerült feloldani a címet: {start_address}")
        return

    e_lat, e_lon, e_disp = geocode_address(end_address)
    if not e_lat:
        print(f"❌ Nem sikerült feloldani a címet: {end_address}")
        return

    print(f"✓ Kiindulópont: {s_disp} ({s_lat:.4f}, {s_lon:.4f})")
    print(f"✓ Célpont:       {e_disp} ({e_lat:.4f}, {e_lon:.4f})\n")

    conn = sqlite3.connect(DB_PATH)

    # 2. Find nearby stops
    orig_stops = find_nearest_stops(conn, s_lat, s_lon, max_dist_km=2.0, limit=8)
    dest_stops = find_nearest_stops(conn, e_lat, e_lon, max_dist_km=2.0, limit=8)

    if not orig_stops:
        print("❌ Nem található tömegközlekedési megálló a kiindulási cím közelében.")
        return
    if not dest_stops:
        print("❌ Nem található tömegközlekedési megálló a célállomás közelében.")
        return

    print(f"Megállók a kiindulásnál: {', '.join(dict.fromkeys([s['stop_name'] for s in orig_stops[:2]]))}")
    print(f"Megállók a célpontnál:    {', '.join(dict.fromkeys([s['stop_name'] for s in dest_stops[:2]]))}\n")

    # 3. Direct route search on gtfs_date
    routes = find_direct_connections(conn, orig_stops, dest_stops, dep_time_str, gtfs_date)

    # 4. Strict transfer route search on gtfs_date
    transfers = find_strict_transfer_connections(conn, orig_stops, dest_stops, dep_time_str, gtfs_date)

    if not routes and not transfers:
        print(f"⚠️ Nem található közlekedő járat ezen a napon ({readable_date}, {day_name}) a megadott időpontban.")
        return

    print("-------------------------------------------------------")
    print(f"🏆 AJÁNLOTT MENETREND {readable_date.upper()} ({day_name.upper()}I NAPRA):")
    print("-------------------------------------------------------")

    if routes:
        r = routes[0]
        o_stop = r['orig_stop']
        d_stop = r['dest_stop']
        print(f"🚶 1. Gyaloglás a megállóhoz:")
        print(f"   {start_address} ➔ {o_stop['stop_name']} ({o_stop['walk_dist_km']:.2f} km, kb. {int(round(o_stop['walk_min']))} perc)")
        print(f"\n🚌 2. Utazás közvetlen járattal:")
        print(f"   [{r['route_short']}] ({r['headsign']})")
        print(f"   Felszállás:  {r['dep_time'][:5]}  |  {o_stop['stop_name']}")
        print(f"   Leszállás:   {r['arr_time'][:5]}  |  {d_stop['stop_name']}")
        print(f"\n🚶 3. Gyaloglás a célig:")
        print(f"   {d_stop['stop_name']} ➔ {end_address} ({d_stop['walk_dist_km']:.2f} km, kb. {int(round(d_stop['walk_min']))} perc)")
        
        arr_h, arr_m, _ = map(int, r['arr_time'].split(':'))
        final_min = arr_m + int(round(d_stop['walk_min']))
        final_h = arr_h + (final_min // 60)
        final_min = final_min % 60
        print(f"\n⏱️  Becsült célbaérkezés: {final_h:02d}:{final_min:02d}")

    elif transfers:
        best = transfers[0]
        l1 = best['leg1']
        tw = best['transfer_walk']
        l2 = best['leg2']
        o_stop = l1['orig_stop']
        d_stop = l2['dest_stop']

        print(f"🚶 1. Gyaloglás a megállóhoz:")
        print(f"   {start_address} ➔ {o_stop['stop_name']} ({o_stop['walk_dist_km']:.2f} km, kb. {int(round(o_stop['walk_min']))} perc)")
        
        print(f"\n🚆 2. Első járat:")
        print(f"   [{l1['route_short']}] ({l1['headsign']})")
        print(f"   Indulás:  {l1['dep_time'][:5]}  |  {o_stop['stop_name']}")
        print(f"   Érkezés:  {l1['arr_time'][:5]}  |  {l1['dest_stop']}")
        
        print(f"\n🚶 3. Valós átszállási séta a csomóponton belül:")
        if tw['dist_m'] < 50:
            print(f"   Azonos megálló / peron ({tw['dist_m']} m)")
        else:
            print(f"   {tw['from_stop']} ➔ {tw['to_stop']}")
            print(f"   Séta: {tw['dist_m']} méter (kb. {tw['walk_min']} perc séta + biztonsági puffer)")
        
        print(f"\n🚌 4. Második járat:")
        print(f"   [{l2['route_short']}] ({l2['headsign']})")
        print(f"   Indulás:  {l2['dep_time'][:5]}  |  {l2['orig_stop']}")
        print(f"   Érkezés:  {l2['arr_time'][:5]}  |  {d_stop['stop_name']}")
        
        print(f"\n🚶 5. Gyaloglás a végcélhoz:")
        print(f"   {d_stop['stop_name']} ➔ {end_address} ({d_stop['walk_dist_km']:.2f} km, kb. {int(round(d_stop['walk_min']))} perc)")
        
        arr_h, arr_m, _ = map(int, l2['arr_time'].split(':'))
        final_min = arr_m + int(round(d_stop['walk_min']))
        final_h = arr_h + (final_min // 60)
        final_min = final_min % 60
        print(f"\n⏱️  Becsült célbaérkezés a végcímre: {final_h:02d}:{final_min:02d}")

    print("=======================================================\n")

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else "Pomáz, HÉV-állomás"
    end = sys.argv[2] if len(sys.argv) > 2 else "2097 Pilisborosjenő Fürdő köz 1."
    dep_time = sys.argv[3] if len(sys.argv) > 3 else "08:00:00"
    date_arg = sys.argv[4] if len(sys.argv) > 4 else "ma"
    plan_journey(start, end, dep_time, date_arg)
