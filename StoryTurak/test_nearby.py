import requests
import json

# Test the /world/nearby endpoint
url = "http://localhost:8001/world/nearby"
params = {"lat": 47.4949, "lon": 19.0417}

try:
    # Note: This will fail if authentication is required
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Zones: {len(data.get('zones', []))}")
        print(f"Total Encounters: {len(data.get('encounters', []))}")
        
        print("\n=== Encounters ===")
        for enc in data.get('encounters', []):
            print(f"  - {enc['id']}: {enc.get('title', 'N/A')}")
        
        # Check if tutorial encounter is present
        tutorial_found = any(e['id'] == 'enc_tutorial_dummy' for e in data.get('encounters', []))
        if tutorial_found:
            print("\n✅ Tutorial encounter FOUND in response!")
        else:
            print("\n❌ Tutorial encounter NOT FOUND in response!")
    else:
        print(f"Error: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend (is it running?)")
except Exception as e:
    print(f"❌ Error: {e}")
