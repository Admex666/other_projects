from geoguessr_api import Geoguessr
import json

ncfa = "hkHei81otr+DKGqHLswnHJfiCWe8en/jlHuOGhEMAkA=JlEiv2LeAwr+KLrpxEZUvLsIcwstOkeW4KhsqlaZ0pKZJYVeSdNEp3vWmRB5NmZ+WlCKu4AzdFLmJ6wgoMCIQ9sB645N+EFuJ8VrsbCJPLQ="
client = Geoguessr(ncfa)

token_duel = "69da3b555b3a5b0d5737e93a"

endpoints = [
    f"https://www.geoguessr.com/api/v3/games/{token_duel}",
    f"https://www.geoguessr.com/api/v4/multiplayer/{token_duel}",
    f"https://www.geoguessr.com/api/v4/multiplayer/result/{token_duel}",
    f"https://www.geoguessr.com/api/v4/multiplayer/results/{token_duel}",
    f"https://www.geoguessr.com/api/v4/multiplayer/duel/{token_duel}/summary",
]

for url in endpoints:
    print(f"Testing {url}...")
    response = client.session.get(url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        break
