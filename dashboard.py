from flask import Blueprint, render_template, session, redirect
from firebase_admin import firestore

# Blueprint
dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")

@dashboard_bp.route("/dashboard")
def dashboard():
    from flask import session, redirect, render_template

    user_id = session.get("user_id")
    
    if not session.get("user_id"):
    # TEMP: allow open access for now
        session['user_id'] = "test-user"

    db = firestore.client()  # ✅ Moved inside function to avoid circular import
    links_ref = db.collection("users").document(user_id).collection("links").order_by("created_at", direction=firestore.Query.DESCENDING)
    links = [doc.to_dict() for doc in links_ref.stream()]
    return render_template("dashboard.html", links=links)


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
