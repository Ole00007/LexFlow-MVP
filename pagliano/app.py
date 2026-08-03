"""
Pagliano Law Firm — Landing Page Flask App
Serves the landing page. /api/intake proxies to the production CRM on Railway.
"""
import os
import urllib.request
import json
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# ── Production CRM intake endpoint ────────────────────────────────────────────
# Local app.py acts as a CORS-safe proxy so the browser form on localhost
# can reach the production CRM without CORS issues.
PRODUCTION_INTAKE_URL = os.environ.get(
    "PRODUCTION_INTAKE_URL",
    "https://web-production-ab54f.up.railway.app/api/intake",
)

app = Flask(__name__,
            template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pagliano-dev-secret")

CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/")
def index():
    return render_template("pagliano.html")


@app.route("/api/intake", methods=["POST"])
def intake():
    """
    Proxy /api/intake to the production CRM on Railway.
    This avoids CORS issues: the browser posts to localhost,
    our Flask app forwards to Railway, and returns the result.
    """
    # Forward the entire request body and form data to Railway
    headers = {"Content-Type": request.content_type or "application/x-www-form-urlencoded"}

    try:
        # Read the body exactly once
        body = request.get_data()

        # Build the urllib request
        req = urllib.request.Request(
            PRODUCTION_INTAKE_URL,
            data=body,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read()
            status = resp.status
            data = json.loads(resp_body)

        return jsonify(data), status

    except urllib.error.HTTPError as exc:
        return jsonify({"error": "Internal server error", "detail": str(exc)}), exc.code
    except Exception as exc:
        return jsonify({"error": "Connection error", "detail": str(exc)}), 502


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
