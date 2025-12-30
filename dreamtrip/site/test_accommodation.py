import requests
import re

def test_cozy():
    url = "https://www.cozycozy.com/en/search/Budapest%2C%20Hungary/2024-06-01/2024-06-05/1-2-0/results"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching cozycozy HTML...")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        
        # Look for searchId
        match = re.search(r"searchId=([A-Za-z0-9]+)", r.text)
        if match:
             print(f"Found searchId in HTML: {match.group(1)}")
        else:
             print("searchId NOT found in HTML via regex")
             
             # Try finding in other ways (scripts)
             if "searchId" in r.text:
                 print("String 'searchId' exists in response.")
             else:
                 print("'searchId' string not found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cozy()
