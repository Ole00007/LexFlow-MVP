"""Unified WSGI entry point — boots CRM + legacy LexFlow intake on one Flask instance."""
import os
from pathlib import Path

from crm import create_app
from app import (
    index, submit, status, admin, admin_matter, uploaded_file, load_demo,
)

# ── Create the CRM app (initialises db, migrate, jwt) ────────────────────────
app = create_app()

# ── Multiple template directories ─────────────────────────────────────────────
# Legacy templates: templates/ (index, admin, status, etc.)
# CRM templates:     crm/templates/ (kanban.html)
# Flask only allows one template_folder, so we use a custom Jinja2 loader.
_jinja_dirs = [
    str(Path(__file__).parent / "templates"),
    str(Path(__file__).parent / "crm" / "templates"),
]
app.jinja_loader = __import__("jinja2").ChoiceLoader([
    __import__("jinja2").FileSystemLoader(d) for d in _jinja_dirs
])

# ── Secret key for flash messages (CRM's Config sets JWT_SECRET_KEY but not Flask's) ──
app.secret_key = os.environ.get("WEBHOOK_SECRET", "dev-secret-change-me")

# ── Register legacy routes on the CRM app ─────────────────────────────────────
# Using add_url_rule + explicit endpoint names so route() and view_func() share
# a single Flask instance but each handler keeps its own function name for
# url_for() calls inside the legacy templates.
app.add_url_rule("/", endpoint="index", view_func=index)
app.add_url_rule("/submit", endpoint="submit", view_func=submit, methods=["POST"])
app.add_url_rule("/status/<token>", endpoint="status", view_func=status)
app.add_url_rule("/admin", endpoint="admin", view_func=admin)
app.add_url_rule(
    "/admin/matter/<int:matter_id>",
    endpoint="admin_matter",
    view_func=admin_matter,
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/uploads/<path:filename>",
    endpoint="uploaded_file",
    view_func=uploaded_file,
)
app.add_url_rule(
    "/admin/load-demo",
    endpoint="load_demo",
    view_func=load_demo,
    methods=["GET", "POST"],
)

# ── Entry point for gunicorn + local dev ──────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
