# smartlinks.py

from flask import Blueprint, render_template, request, session, redirect

import uuid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from flask import url_for

import os

# === Blueprint setup ===
smartlink_bp = Blueprint("smartlinks", __name__, template_folder="templates")

# === Spotify API Setup ===
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET")
))

# === Firebase Setup ===
if not firebase_admin._apps:  # Prevent reinitializing in multi-blueprint apps
    cred = credentials.Certificate("firebase_key.json")  # Make sure this is in .gitignore!
    firebase_admin.initialize_app(cred)

db = firestore.client()

# === Helper function ===
def extract_playlist_metadata(playlist_url):
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist = sp.playlist(playlist_id)
    return {
        "name": playlist["name"],
        "cover": playlist["images"][0]["url"],
        "url": playlist["external_urls"]["spotify"]
    }

# === Routes ===

@smartlink_bp.route("/smartlink", methods=["GET", "POST"])
def create_smartlink():
    if request.method == "POST":
        playlist_url = request.form.get("playlist_url", "").strip()
        if not playlist_url:
            return "Missing playlist URL", 400

        metadata = extract_playlist_metadata(playlist_url)
        slug = str(uuid.uuid4())[:6]


        db.collection("smartlinks").document(slug).set({
            "slug": slug,
            "name": metadata["name"],
            "cover": metadata["cover"],
            "url": metadata["url"],
            "created_at": firestore.SERVER_TIMESTAMP  # ✅ this is the fix
        })


        link = f"https://spotify-smartlink-tracker.onrender.com/s/{slug}"
        return render_template("smartlink_success.html", link=link)
    return render_template("home.html")

@smartlink_bp.route("/s/<slug>")
def smartlink_page(slug):
    doc = db.collection("smartlinks").document(slug).get()
    if not doc.exists:
        return "Smartlink not found 😢", 404

    data = doc.to_dict()

    # ✅ Always render landing page, don’t auto-redirect
    return render_template("smartlink.html", data=data)


# @smartlink_bp.route("/s/<slug>")
# def smartlink_page(slug):
#     from flask import session, redirect, request

#     doc = db.collection("smartlinks").document(slug).get()
#     if not doc.exists:
#         return "Smartlink not found 😢", 404

#     data = doc.to_dict()

#     # ✅ Debug: print session content
#     print("SESSION STATE:", session)

#     if "user_id" in session:
#         return redirect(data["url"])
    
#     # 🚨 Enforce login: redirect to Spotify auth
#     session["smartlink_id"] = slug
#     return redirect(f"/login?from={slug}")


