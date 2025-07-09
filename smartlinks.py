# smartlinks.py

from flask import Blueprint, render_template, request
import uuid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import firebase_admin
from firebase_admin import credentials, firestore
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
            "url": metadata["url"]
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
    return render_template("smartlink.html", data=data)
