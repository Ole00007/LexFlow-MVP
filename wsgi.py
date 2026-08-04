"""Unified WSGI entry point — boots CRM + legacy LexFlow intake on one Flask instance."""
import os
from pathlib import Path

from crm import create_app
from app import (
    index, submit, status, admin, admin_matter, uploaded_file, load_demo,
    login, logout, api_token, kanban_view, dashboard_view,
)

# ── Create the CRM app (initialises db, migrate, jwt) ────────────────────────
app = create_app()

# ── Run migrations on startup ───────────────────────────────────────────────
import os
try:
    from alembic.config import Config
    from alembic import command
    with app.app_context():
        os.chdir("migrations")
        alembic_cfg = Config("alembic.ini")
        # Guard against concurrent migration runs (gunicorn spawns 2 workers,
        # and the Procfile also runs `alembic upgrade head`). PostgreSQL
        # advisory lock makes the upgrade single-flight per DB.
        db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_url.startswith("postgres"):
            from sqlalchemy import text
            from crm.extensions import db as crm_db
            conn = crm_db.engine.connect()
            try:
                conn.execute(text("SELECT pg_advisory_lock(724391)"))
                command.upgrade(alembic_cfg, "head")
            finally:
                conn.execute(text("SELECT pg_advisory_unlock(724391)"))
                conn.close()
        else:
            command.upgrade(alembic_cfg, "head")
        print("Migrations applied successfully")
        os.chdir("..")
except Exception as e:
    print(f"Migration warning: {e}")
    # Continue anyway - the app might work with existing schema

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

# ── Seed admin user from env (idempotent) ─────────────────────────────────────
# Set ADMIN_EMAIL + ADMIN_PASSWORD on the host to create/keep Diego's account.
try:
    with app.app_context():
        from crm.models.user import User
        from crm.extensions import db
        admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
        if admin_email and admin_password:
            existing = User.query.filter_by(email=admin_email).first()
            if not existing:
                u = User(email=admin_email, role="admin")
                u.set_password(admin_password)
                db.session.add(u)
                db.session.commit()
                print(f"Seeded admin user: {admin_email}")
            else:
                print(f"Admin user exists: {admin_email}")
except Exception as e:
    print(f"Admin seed warning: {e}")

# ── Register legacy routes on the CRM app ─────────────────────────────────────
# Using add_url_rule + explicit endpoint names so route() and view_func() share
# a single Flask instance but each handler keeps its own function name for
# url_for() calls inside the legacy templates.
app.add_url_rule("/", endpoint="index", view_func=index)
app.add_url_rule("/login", endpoint="login", view_func=login, methods=["GET", "POST"])
app.add_url_rule("/logout", endpoint="logout", view_func=logout)
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
app.add_url_rule("/kanban", endpoint="kanban_view", view_func=kanban_view)
app.add_url_rule("/dashboard", endpoint="dashboard_view", view_func=dashboard_view)
app.add_url_rule("/api/token", endpoint="api_token", view_func=api_token)

# ── Entry point for gunicorn + local dev ──────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
