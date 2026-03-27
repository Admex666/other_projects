import time
import requests
from bs4 import BeautifulSoup
import tls_client
import random

def test_tcdb_requests_speed(player_name):
    session = tls_client.Session(client_identifier="chrome_120")
    search_query = player_name.replace(" ", "+")
    url = f"https://www.tcdb.com/Search.cfm?SearchCategory=Soccer&q={search_query}"
    
    print(f"Testing TCDB (Requests-based) for: {player_name}")
    start = time.time()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = session.get(url, headers=headers)
        duration = time.time() - start
        print(f"Status: {resp.status_code}, Time: {duration:.2f}s")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Check if we landed on search results or a direct profile
            links = soup.find_all('a', href=True)
            profile_links = [l['href'] for l in links if 'Person.cfm' in l['href']]
            if profile_links:
                print(f"Found {len(profile_links)} profile links. First: {profile_links[0]}")
            else:
                print("No direct profile links found in initial HTML (might be JS-rendered search results)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tcdb_requests_speed("Erling Haaland")
    test_tcdb_requests_speed("Lamine Yamal")
