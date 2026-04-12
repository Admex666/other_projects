from geoguessr_api import Geoguessr
import json

# Your session cookie
ncfa = "hmKpeRRSW3xcGFxSJ7sWUaOIEqBLueXjbIt46+hJvMg=JlEiv2LeAwr+KLrpxEZUvLsIcwstOkeW4KhsqlaZ0pKZJYVeSdNEp3vWmRB5NmZ+WlCKu4AzdFLmJ6wgoMCIQ6YYN10tYP+1zkxlacyZTpQ="
client = Geoguessr(ncfa)

def save_data(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data saved to {filename}")

# 1. Challenge Data
token_challenge = "PXI676ChCvbbTv4n"
print(f"Fetching challenge data for: {token_challenge}")
url_challenge = f"https://www.geoguessr.com/api/v3/games/{token_challenge}"
response = client.session.get(url_challenge)
if response.status_code == 200:
    save_data(response.json(), f"challenge_{token_challenge}.json")
else:
    print(f"Challenge error: {response.status_code}")

# 2. Duel Data (using the fixed game-server endpoint)
token_duel = "69da3b555b3a5b0d5737e93a"
print(f"\nFetching duel data for: {token_duel}")
try:
    duel_data = client.get_duel_info(token_duel)
    save_data(duel_data, f"duel_{token_duel}.json")
except Exception as e:
    print(f"Duel error: {e}")