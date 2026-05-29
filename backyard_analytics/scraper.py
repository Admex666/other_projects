import urllib.request
import urllib.parse
import json
import time
import csv
import os

EVENT_ID = 392799
BASE_URL = "https://my3.raceresult.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    print(f"=== Starting Backyard Ultra Scraper for Event {EVENT_ID} ===")
    
    # 1. Fetch config to get the live key
    config_url = f"{BASE_URL}/{EVENT_ID}/results/config"
    print("Fetching event configuration...")
    config = fetch_json(config_url)
    if not config:
        print("Failed to fetch event configuration.")
        return
    
    key = config.get("key")
    event_name = config.get("eventname", "Backyard Ultra")
    print(f"Successfully loaded configuration for '{event_name}'")
    print(f"API Key: {key}")
    
    # 2. Fetch overall results
    # We use the list name from the config or absolute results list ID 'FD0C8A'
    listname = "Result Lists|Backyard abszolút eredmények"
    params = {
        "key": key,
        "listname": listname,
        "page": "results",
        "contest": "0",
        "r": "all"
    }
    overall_url = f"{BASE_URL}/{EVENT_ID}/results/list?{urllib.parse.urlencode(params)}"
    print("\nFetching overall results...")
    overall_data = fetch_json(overall_url)
    if not overall_data or "data" not in overall_data:
        print("Failed to fetch overall results.")
        return
    
    fields = overall_data.get("DataFields", [])
    rows = overall_data.get("data", [])
    print(f"Found {len(rows)} participants.")
    
    # Save overall results to CSV
    os.makedirs("data", exist_ok=True)
    overall_csv_path = "data/overall_results.csv"
    with open(overall_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    print(f"Saved overall results to {overall_csv_path}")
    
    # 3. Extract participant IDs and scrape detailed lap times
    # From our analysis:
    # Index 0 of fields is 'BIB'
    # Index 1 of fields is 'ID' (this is the PID used in details)
    # Let's find the column index for ID and DisplayName
    try:
        id_col_idx = fields.index("ID")
    except ValueError:
        id_col_idx = 1  # Default fallback
        
    try:
        name_col_idx = fields.index("DisplayName")
    except ValueError:
        name_col_idx = 4  # Default fallback
        
    detailed_laps = []
    
    print("\nScraping detailed lap times for each participant...")
    print("NOTE: Respecting the rate limits (1-second delay between requests) to prevent blockages.")
    
    for idx, row in enumerate(rows):
        pid = row[id_col_idx]
        name = row[name_col_idx].strip()
        laps_str = row[fields.index('[BackyardNumberOfLaps]&" k\u00f3r"')] if '[BackyardNumberOfLaps]&" k\u00f3r"' in fields else "0"
        print(f"[{idx+1}/{len(rows)}] Scraping {name} (PID: {pid}, {laps_str})...")
        
        lap_params = {
            "key": key,
            "listname": "Result Lists|Lap Details Backyard",
            "page": "details1",
            "r": "pid",
            "pid": pid
        }
        lap_url = f"{BASE_URL}/{EVENT_ID}/details1/list?{urllib.parse.urlencode(lap_params)}"
        
        lap_data = fetch_json(lap_url)
        if lap_data and "data" in lap_data:
            lap_rows = lap_data["data"]
            # Save raw individual JSON
            with open(f"data/laps_pid_{pid}.json", "w", encoding="utf-8") as f:
                json.dump(lap_data, f, ensure_ascii=False, indent=4)
                
            # Add to master list
            # lap_rows format: ['BIB', 'ID', 'LapNumber', 'LapTime', 'Pace']
            # Let's inspect the headers from the lap_data response
            lap_fields = lap_data.get("DataFields", ["BIB", "ID", "Lap", "LapTime", "Pace"])
            for lap_row in lap_rows:
                # Build a clean dictionary for easier pandas/analysis loading
                lap_dict = {
                    "PID": pid,
                    "Name": name,
                    "BIB": lap_row[0] if len(lap_row) > 0 else "",
                    "Lap": lap_row[2] if len(lap_row) > 2 else "",
                    "LapTime": lap_row[3] if len(lap_row) > 3 else "",
                    "Pace": lap_row[4] if len(lap_row) > 4 else ""
                }
                detailed_laps.append(lap_dict)
        else:
            print(f"  Warning: Failed to fetch laps for {name}")
            
        # Polite delay to respect RaceResult rate limiting (1 request per second)
        time.sleep(1.1)
        
    # Save all detailed laps to CSV
    detailed_csv_path = "data/detailed_laps.csv"
    if detailed_laps:
        with open(detailed_csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["PID", "Name", "BIB", "Lap", "LapTime", "Pace"])
            writer.writeheader()
            writer.writerows(detailed_laps)
        print(f"\nSuccessfully scraped and saved detailed laps to {detailed_csv_path}")
    else:
        print("\nNo detailed lap times were scraped.")
        
    print("\n=== Scraping Completed Successfully! ===")

if __name__ == "__main__":
    main()
