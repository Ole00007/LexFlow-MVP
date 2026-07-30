"""
Pagliano Law Firm — Landing Page Flask App
Serves the landing page and provides the /api/intake endpoint.
"""
import os
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__,
            template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pagliano-dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'pagliano.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Import DB models (lazy to avoid circular issues)
from database import db, Contact, Case

db.init_app(app)


@app.route("/")
def index():
    return render_template("pagliano.html")


@app.route("/api/intake", methods=["POST"])
def intake():
    """
    Landing-page intake endpoint.
    Accepts FormData (x-www-form-urlencoded or multipart).
    Creates a Contact and an optional Case record.
    """
    data = request.form or request.get_json(silent=True) or {}
    if isinstance(data, dict):
        fullname = data.get("fullname", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        message = data.get("message", "").strip()
        gdpr = data.get("gdpr_consent", "")
        source = data.get("source", "pagliano_lp")
        practice_area = data.get("practice_area", "")
        urgency = data.get("urgency", "medium")
    else:
        # Fallback for formdata-as-object
        fullname = (data.get("fullname") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip()
        message = (data.get("message") or "").strip()
        gdpr = data.get("gdpr_consent", "")
        source = data.get("source", "pagliano_lp")
        practice_area = data.get("practice_area", "")
        urgency = data.get("urgency", "medium")

    # Validate required fields
    errors = []
    if not fullname:
        errors.append("fullname is required")
    if not email:
        errors.append("email is required")
    elif "@" not in email:
        errors.append("email is invalid")
    if gdpr != "true" and gdpr != "True":
        errors.append("gdpr_consent is required")

    if errors:
        return jsonify({"error": errors[0], "detail": errors}), 400

    try:
        contact = Contact(
            fullname=fullname,
            email=email,
            phone=phone or None,
            source=source,
            gdpr_consent=bool(gdpr),
        )
        db.session.add(contact)
        db.session.flush()

        # Create a case if a practice area was selected
        if practice_area:
            case = Case(
                contact_id=contact.id,
                practice_area=practice_area,
                urgency=urgency,
                description=message or None,
            )
            db.session.add(case)

        db.session.commit()
        return jsonify({
            "ok": True,
            "message": "Request submitted successfully.",
            "contact_id": contact.id,
        }), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
