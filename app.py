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

import time

def get_user_info_with_retry(access_token, retries=3, delay=2):
    for i in range(retries):
        user_resp = requests.get(
            "https://api.spotify.com/v1/me",
            headers={ "Authorization": f"Bearer {access_token}" }
        )

        if user_resp.status_code == 429:
            retry_after = int(user_resp.headers.get("Retry-After", delay))
            print(f"Rate limited. Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            return user_resp
    return user_resp  # return last response even if still 429


@app.route('/login')
def login():
    from_link = request.args.get("from")  # e.g., abc123
    if from_link:
        session['smartlink_id'] = from_link

    auth_query = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "show_dialog": "true"  # 🔁 Force Spotify to show login prompt
    }
    url = f"{AUTH_URL}?{urlencode(auth_query)}"
    return redirect(url)

@app.route('/debug')
def debug():
    try:
        raise Exception("🔥 Manual debug error to test error handling")
    except Exception as e:
        import traceback
        return f"<h3>DEBUG ERROR:</h3><pre>{str(e)}\n\n{traceback.format_exc()}</pre>", 500

@app.route('/callback')
def callback():
    try:
        code = request.args.get('code')
        if not code:
            return "<h3>❌ Missing authorization code. Please go through the smartlink again.</h3>", 400

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
            return f"<h3>❌ Spotify token exchange failed:</h3><pre>{r.status_code} - {r.text}</pre>", 400

        token_info = r.json()
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")

        if not access_token:
            return "<h3>❌ Access token missing. Please retry.</h3>", 400

        user_resp = get_user_info_with_retry(access_token)

        if user_resp.status_code != 200:
            return f"<h3>❌ Failed to fetch Spotify user:</h3><pre>{user_resp.status_code} - {user_resp.text}</pre>", 400

        user_info = user_resp.json()
        user_id = user_info.get("id")
        country = user_info.get("country", "unknown")

        if not user_id:
            return "<h3>❌ User ID not found in Spotify response.</h3>", 400

        # ✅ Set user session so future visits skip login
        session['user_id'] = user_id

        smartlink_id = session.get('smartlink_id', 'unknown')

        # Prepare user data
        user_data = {
            "display_name": user_info.get("display_name"),
            "email": user_info.get("email"),
            "smartlink_id": smartlink_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "country": country,  # ✅ Save country
            "last_login": str(datetime.utcnow())
        }

        # Save to Firestore
        db.collection("users").document(user_id).set(user_data)

        # Lookup smartlink URL from slug
        if smartlink_id != "unknown":
            doc = db.collection("smartlinks").document(smartlink_id).get()
            if doc.exists:
                playlist_url = doc.to_dict()["url"]
                session.pop("smartlink_id", None)  # Clear after use
                return redirect(playlist_url)

        # fallback: go to dashboard
        return redirect("/dashboard")

    except Exception as e:
        import traceback
        return f"<h3>❌ Unexpected Error:</h3><pre>{str(e)}\n\n{traceback.format_exc()}</pre>", 500

@app.route('/admin/users')
def list_users():
    users_ref = db.collection("users").stream()
    output = {doc.id: doc.to_dict() for doc in users_ref}
    return json.dumps(output, indent=2), 200, {'Content-Type': 'application/json'}

@app.route("/logout")
def logout():
    session.clear()
    return "✅ Session cleared. You can now test login again."


# ✅ Admin-only route to get latest user log
@app.route('/admin/users-latest')
def admin_user_log():
    if os.path.exists("user_snapshot.json"):
        with open("user_snapshot.json", "r") as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({"error": "No user log found"}), 404, {'Content-Type': 'application/json'}

import os
from smartlinks import smartlink_bp
app.register_blueprint(smartlink_bp)
from dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
