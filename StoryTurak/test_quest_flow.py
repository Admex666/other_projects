
import requests
import sys

BASE_URL = "http://localhost:8001"
USERNAME = "test"
PASSWORD = "tesz"

def login():
    url = f"{BASE_URL}/auth/token"
    # Using data dict implies application/x-www-form-urlencoded
    data = {"username": USERNAME, "password": PASSWORD}
    print(f"Logging in to {url}...")
    try:
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            print(f"Login success. Token: {token[:10]}...")
            return token
        else:
            print(f"Login failed: {resp.status_code} {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

def reset_quests(token):
    print("Resetting quests...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/debug/reset_quests", headers=headers)
    print(f"Reset: {resp.status_code} {resp.json()}")

def resolve_encounter(token, enc_id):
    print(f"Resolving encounter: {enc_id}")
    headers = {"Authorization": f"Bearer {token}"}
    data = {"encounter_id": enc_id, "outcome": "success"}
    resp = requests.post(f"{BASE_URL}/encounters/resolve", json=data, headers=headers)
    print(f"Resolve: {resp.status_code} {resp.json()}")

def get_my_quests(token):
    print("Fetching user quests...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/characters", headers=headers)
    # Actually need char ID to get quests usually, but let's assume /quests/{id} or check logic
    # In main.py: /characters/{char_id}/quests
    # First get chars
    chars = resp.json()
    if not chars:
        print("No characters found. Creating one...")
        # Create char
        cdata = {"character_class": "SOLDIER", "name": "TestHero"}
        resp = requests.post(f"{BASE_URL}/characters/create?character_class=SOLDIER&name=TestHero", headers=headers)
        char_id = resp.json()["id"]
    else:
        char_id = chars[0]["id"]
    
    print(f"Checking quests for char {char_id}")
    resp = requests.get(f"{BASE_URL}/characters/{char_id}/quests", headers=headers)
    print(f"Quests: {resp.json()}")

if __name__ == "__main__":
    token = login()
    reset_quests(token)
    
    # Simulate resolving the specific quest start encounter
    target_enc_id = "quest_botanic_garden_enc_nervous_gardener"
    resolve_encounter(token, target_enc_id)
    
    # Check results
    get_my_quests(token)
