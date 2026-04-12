from geoguessr_api import Geoguessr
import json

ncfa = "hkHei81otr+DKGqHLswnHJfiCWe8en/jlHuOGhEMAkA=JlEiv2LeAwr+KLrpxEZUvLsIcwstOkeW4KhsqlaZ0pKZJYVeSdNEp3vWmRB5NmZ+WlCKu4AzdFLmJ6wgoMCIQ9sB645N+EFuJ8VrsbCJPLQ="
client = Geoguessr(ncfa)

# Get current user profile to get ID
r = client.session.get("https://www.geoguessr.com/api/v3/profiles/")
if r.status_code == 200:
    profile = r.json()
    user_id = profile["user"]["id"]
    print(f"User ID: {user_id}")
    
    # Get recent games
    # Try different history endpoints
    history_urls = [
        f"https://www.geoguessr.com/api/v4/feed/private?count=100",
    ]
    
    for url in history_urls:
        print(f"Testing {url}...")
        res = client.session.get(url)
        if res.status_code == 200:
            print(f"Success! Found {len(res.json())} items.")
            # Save a sample to inspect
            with open("history_sample.json", "w") as f:
                json.dump(res.json(), f, indent=4)
        else:
            print(f"Failed: {res.status_code}")
else:
    print(f"Failed to get profile: {r.status_code}")
