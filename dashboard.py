from flask import Blueprint, render_template, session, redirect
from firebase_admin import firestore

# Blueprint
dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")
db = firestore.client()

@dashboard_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    links_ref = db.collection("users").document(user_id).collection("links").order_by("created_at", direction=firestore.Query.DESCENDING)
    links = [doc.to_dict() for doc in links_ref.stream()]

    return render_template("dashboard.html", links=links)

@app.route('/delete/<slug>', methods=["POST"])
def delete_link(slug):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    doc_ref = db.collection("users").document(user_id).collection("links").document(slug)
    doc_ref.delete()
    return redirect("/dashboard")
