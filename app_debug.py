"""Debug endpoint for route inspection — remove after diagnosis."""
from flask import Blueprint, jsonify
import sys

# This script runs standalone to test app.py routes
from app import app as flask_app

debug_bp = Blueprint("debug", __name__)

@debug_bp.route("/__routes")
def list_routes():
    rules = sorted([str(r) for r in flask_app.url_map.iter_rules()])
    return jsonify({
        "routes": rules,
        "count": len(rules),
        "python": sys.version,
    })

app.register_blueprint(debug_bp)

# Also print when run directly
if __name__ == "__main__":
    with flask_app.test_client() as c:
        resp = c.get("/__routes")
        print(resp.get_json())