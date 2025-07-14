from flask import Blueprint, render_template, session, redirect

# Blueprint
dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")  # Make sure path is correct
    firebase_admin.initialize_app(cred)

db = firestore.client()

@dashboard_bp.route("/dashboard")
def dashboard():
    from flask import session, redirect, render_template

    user_id = session.get("user_id")
    
    if not session.get("user_id"):
    # TEMP: allow open access for now
        session['user_id'] = "test-user"

    db = firestore.client()  # ✅ Moved inside function to avoid circular import
    docs = db.collection("smartlinks").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    links = [doc.to_dict() | {"id": doc.id} for doc in docs]
    return render_template("dashboard.html", links=links)

@dashboard_bp.route("/smartlink/<slug>/metrics")
def smartlink_metrics(slug):
    doc = db.collection("smartlinks").document(slug).get()
    if not doc.exists:
        return "Smartlink not found", 404
    data = doc.to_dict()

    # Dummy data (replace with actual metrics when implemented)
    metrics = {
        "views": 362_300,
        "clicks": 271_000,
        "ctr": 74.79,
        "followers": 53_100,
        "listeners": 109_000,
        "streams": 3_200_000,
        "s_l": 29.04,
        "countries": [
            {"name": "Colombia", "followers": 3430, "listeners": 8680, "streams": 260928, "spl": 30.06},
            {"name": "Morocco", "followers": 2012, "listeners": 5865, "streams": 238869, "spl": 40.39},
            # Add more...
        ]
    }

    return render_template("metrics.html", data=data, metrics=metrics)


@dashboard_bp.route('/delete/<slug>', methods=["POST"])
def delete_link(slug):
    from flask import session, redirect

    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    db = firestore.client()
    doc_ref = db.collection("users").document(user_id).collection("links").document(slug)
    doc_ref.delete()
    return redirect("/dashboard")
