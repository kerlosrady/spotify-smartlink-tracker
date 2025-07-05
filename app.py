import os
import requests
import json
from datetime import datetime
from flask import Flask, redirect, request, session
from dotenv import load_dotenv
from urllib.parse import urlencode

# === Load env vars ===
load_dotenv()
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

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
    try:
        code = request.args.get('code')
        if not code:
            return "<h3>❌ Missing 'code' from Spotify redirect.</h3>", 400

        # Exchange code for access token
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        }

        headers = { "Content-Type": "application/x-www-form-urlencoded" }
        r = requests.post(TOKEN_URL, data=token_data, headers=headers)
        if r.status_code != 200:
            return f"<h3>❌ Spotify token exchange failed:</h3><pre>{r.text}</pre>", 400

        token_info = r.json()
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")

        if not access_token:
            return "<h3>❌ Missing access token in Spotify response.</h3>", 400

        # Get user profile from Spotify
        user_resp = requests.get(
            "https://api.spotify.com/v1/me",
            headers={ "Authorization": f"Bearer {access_token}" }
        )
        if user_resp.status_code != 200:
            return f"<h3>❌ Spotify user info fetch failed:</h3><pre>{user_resp.text}</pre>", 400

        user_info = user_resp.json()
        user_id = user_info.get('id')
        if not user_id:
            return "<h3>❌ Could not extract Spotify user ID.</h3>", 400

        smartlink_id = session.get('smartlink_id', 'unknown')

        user_data = {
            "display_name": user_info.get("display_name"),
            "email": user_info.get("email"),
            "smartlink_id": smartlink_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "last_login": str(datetime.utcnow())
        }

        # Save to Firestore
        try:
            db.collection("users").document(user_id).set(user_data)
        except Exception as db_err:
            print("❌ Firestore error:", db_err)
            return "<h3>❌ Failed to save user to Firestore.</h3>", 500

        return f"""
        <h2>✅ You're connected!</h2>
        <p>Welcome, {user_info.get("display_name") or "user"} 🎧</p>
        <p>Your account has been linked via smartlink <b>{smartlink_id}</b>.</p>
        """

    except Exception as e:
        print("❌ Unexpected error in /callback:", str(e))
        return f"<h3>❌ Unexpected error occurred:</h3><pre>{str(e)}</pre>", 500


@app.route('/admin/users')
def list_users():
    users_ref = db.collection("users").stream()
    output = {doc.id: doc.to_dict() for doc in users_ref}
    return json.dumps(output, indent=2), 200, {'Content-Type': 'application/json'}


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
