import json
import requests
from datetime import datetime

DB_FILE = "users.json"
STREAM_LOG = "streams.json"

# Load saved users
with open(DB_FILE, 'r') as f:
    users = json.load(f)

all_streams = {}

for user_id, info in users.items():
    print(f"\n🎧 Checking user: {info['display_name']} (from smartlink: {info['smartlink_id']})")

    access_token = info['access_token']

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(
            "https://api.spotify.com/v1/me/player/recently-played?limit=10",
            headers=headers
        )

        data = response.json()

        user_streams = []
        for item in data.get("items", []):
            track = item['track']
            played_at = item['played_at']
            user_streams.append({
                "track_name": track['name'],
                "artist": track['artists'][0]['name'],
                "played_at": played_at,
                "smartlink_id": info['smartlink_id']
            })
            print(f"  ✅ {track['name']} by {track['artists'][0]['name']} at {played_at}")

        all_streams[user_id] = user_streams

    except Exception as e:
        print(f"⚠️ Error with user {user_id}: {e}")

# Save logs
with open(STREAM_LOG, 'w') as f:
    json.dump(all_streams, f, indent=2)

print("\n🎯 Done! All stream logs saved to streams.json")
