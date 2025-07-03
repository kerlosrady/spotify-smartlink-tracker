import requests
import json

playlist_id = "0xF0eHm3eguBqBvgVyQ3UB"
access_token = "BQCbfMTBhIBqGxGMIlQjhTa2H32fsi-3jsDyppsy2oNZwur4fq67bsBJJcwtux5cohE7Thpmps25YwlMLoAvRzRzLVGSoyqq0kkYA4gpa8df3J2QSdAnA0fJBkhFml3_dQ0HUSvz609m3-RKujee0J-En-5W5O4e94O6XPA_argjkvDBJggR-ZPXk4j1iaQ-YDFiTsccp9Ynr4rd0ZKZnt_lB1EmmSEy4plycEvfTYK4svhK0Lv5OPXH9E6_f_-7aZjYN7-QAQ"

headers = {
    "Authorization": f"Bearer {access_token}"
}

all_tracks = []
offset = 0

while True:
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100&offset={offset}"
    res = requests.get(url, headers=headers)
    data = res.json()

    for item in data["items"]:
        if item["track"] is not None:
            all_tracks.append(item["track"]["name"].strip().lower())

    if data["next"] is None:
        break
    offset += 100

with open("playlist_tracks.json", "w") as f:
    json.dump(all_tracks, f, indent=2)

print(f"✅ Saved {len(all_tracks)} track names to playlist_tracks.json")
