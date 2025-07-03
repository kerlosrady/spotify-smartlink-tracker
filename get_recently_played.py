import requests

# Replace this with your actual access token
ACCESS_TOKEN = 'BQCLF8Fh7ADQEMRFnPCMyXINqLnWo0BXJ9xoW4BdnMqGBvzV7WeqoDpW0dBXpusc7OuIBl2Yni8e3qLGU030LprTvv7f4brEMI7SdolBQU9R4WjO2qyH6bqPldGfIJaVpbWaoaHDxALuZFhHtQ47P6NAkaL8-rbbYuuda7e6Gt4C8_M95CCC4q3fntYytX0iV5-1RW7A-hq6n2RgB71jYLgrDbz6OLTR-TqhHtkuiOf5zT_MU5Fj8tM4_4zLs4NbPqNOnpQMzA'

url = 'https://api.spotify.com/v1/me/player/recently-played?limit=10'

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

response = requests.get(url, headers=headers)
data = response.json()

for item in data['items']:
    track = item['track']
    played_at = item['played_at']
    print(f"{track['name']} by {track['artists'][0]['name']} at {played_at}")
