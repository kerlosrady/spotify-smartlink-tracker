import os
import requests
import json
from datetime import datetime
from flask import Flask, redirect, request, session
from dotenv import load_dotenv
from urllib.parse import urlencode

# === Load env vars ===
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# === Spotify API config ===
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "user-read-email user-read-private user-read-recently-played user-read-playback-state"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

DB_FILE = "users.json"
# === Add dump route BEFORE app.run ===
@app.route('/dump-users')
def dump_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({"error": "No users found."}), 404, {'Content-Type': 'application/json'}

# ✅ MISSING ROUTE: handles smartlink clicks like /s/techno-drop
@app.route('/s/<link_id>')
def smartlink_redirect(link_id):
    session['smartlink_id'] = link_id
    return redirect('/login')

# Logs into Spotify
@app.route('/login')
def login():
    auth_query = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }
    url = f"{AUTH_URL}?{urlencode(auth_query)}"
    return redirect(url)


@app.route('/callback')
def callback():
    code = request.args.get('code')

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(TOKEN_URL, data=token_data, headers=headers)
    token_info = r.json()

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    user_info = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    smartlink_id = session.get('smartlink_id', 'unknown')
    user_id = user_info.get('id')

    # Store to admin-only log file
    admin_db = {
        user_id: {
            "display_name": user_info.get("display_name"),
            "email": user_info.get("email"),
            "smartlink_id": smartlink_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "last_login": str(datetime.utcnow())
        }
    }

    with open("user_snapshot.json", "w") as f:
        json.dump(admin_db, f, indent=2)

    return f"""
    <h2>✅ You're connected!</h2>
    <p>Thank you for authorizing the Spotify app.</p>
    <p>You may now continue listening on Spotify. 🎧</p>
    """

# ✅ Admin-only route to get latest user log
@app.route('/admin/users-latest')
def admin_user_log():
    if os.path.exists("user_snapshot.json"):
        with open("user_snapshot.json", "r") as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({"error": "No user log found"}), 404, {'Content-Type': 'application/json'}

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
