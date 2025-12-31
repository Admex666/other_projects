import requests
import json

def check_teleport():
    try:
        url = "https://api.teleport.org/api/urban_areas/slug:barcelona/details/"
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Look for Cost of Living
            for category in data.get("categories", []):
                if category["id"] == "COST-OF-LIVING":
                    print(json.dumps(category, indent=2))
                if category["id"] == "SAFETY":
                    print(json.dumps(category, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_teleport()
