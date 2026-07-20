import os
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_from_directory, abort)
from werkzeug.utils import secure_filename

try:
    import resend
except ImportError:
    resend = None

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / "data" / "app.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "txt"}

resend.api_key       = os.environ.get("RESEND_API_KEY", "")
ADMIN_EMAIL          = os.environ.get("ADMIN_EMAIL", "")
EMAIL_FROM           = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
EMAIL_FROM_NAME      = os.environ.get("EMAIL_FROM_NAME", "LexFlow")
APP_URL              = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:5000")
if not APP_URL.startswith("http"):
    APP_URL = "https://" + APP_URL

PRACTICES = ["Commercial", "Employment", "Real Estate", "Family",
             "Debt Collection", "Shipping / Logistics", "Other"]
STATUSES  = ["New intake", "Conflict check", "Lawyer review",
             "Waiting client docs", "Quoted", "Engaged", "Closed"]

app = Flask(__name__)
app.secret_key = os.environ.get("WEBHOOK_SECRET", "dev-secret-change-me")


# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS matters (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at    TEXT NOT NULL,
            token         TEXT NOT NULL UNIQUE,
            client_name   TEXT NOT NULL,
            email         TEXT NOT NULL,
            phone         TEXT,
            company       TEXT,
            practice_area TEXT NOT NULL,
            urgency       TEXT DEFAULT 'Medium',
            description   TEXT,
            status        TEXT NOT NULL DEFAULT 'New intake',
            internal_notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS documents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            matter_id     INTEGER NOT NULL,
            stored_name   TEXT NOT NULL,
            original_name TEXT NOT NULL,
            uploaded_at   TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            matter_id   INTEGER NOT NULL,
            event_time  TEXT NOT NULL,
            status      TEXT NOT NULL,
            note        TEXT
        );
        """)

init_db()


# ── Email helper ─────────────────────────────────────────────────────────────
def send_intake_notification(matter_id, client_name, email, practice_area, urgency, token):
    if not resend.api_key or not ADMIN_EMAIL:
        print("Email skipped: missing RESEND_API_KEY or ADMIN_EMAIL")
        return
    try:
        resend.Emails.send({
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
            "to":   [ADMIN_EMAIL],
            "subject": f"New intake #{matter_id} – {practice_area} ({urgency})",
            "html": f"""
                <h2>New matter received – LexFlow</h2>
                <p><strong>Matter #:</strong> {matter_id}</p>
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Practice:</strong> {practice_area}</p>
                <p><strong>Urgency:</strong> {urgency}</p>
                <p><strong>Token:</strong> {token}</p>
                <p>
                  <a href="{APP_URL}/admin/matter/{matter_id}"
                     style="background:#2563eb;color:#fff;padding:10px 20px;
                            border-radius:6px;text-decoration:none;">
                    Open in admin →
                  </a>
                </p>
            """
        })
        print(f"Intake email sent for matter #{matter_id}")
    except Exception as e:
        print(f"Email error: {e}")


# ── Util ──────────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", practices=PRACTICES)


@app.route("/submit", methods=["POST"])
def submit():
    client_name   = request.form.get("client_name", "").strip()
    email         = request.form.get("email", "").strip()
    phone         = request.form.get("phone", "").strip()
    company       = request.form.get("company", "").strip()
    practice_area = request.form.get("practice_area", "").strip()
    urgency       = request.form.get("urgency", "Medium").strip()
    description   = request.form.get("description", "").strip()

    if not client_name or not email or not practice_area:
        flash("Name, email, and practice area are required.", "error")
        return redirect(url_for("index"))

    token = secrets.token_hex(8).upper()
    now   = datetime.utcnow().isoformat()

    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO matters
               (created_at, token, client_name, email, phone, company,
                practice_area, urgency, description, status, internal_notes)
               VALUES (?,?,?,?,?,?,?,?,?,'New intake','')""",
            (now, token, client_name, email, phone, company,
             practice_area, urgency, description)
        )
        matter_id = cur.lastrowid
        conn.execute(
            "INSERT INTO events (matter_id, event_time, status, note) VALUES (?,?,?,?)",
            (matter_id, now, "New intake", "Matter created from intake form.")
        )
        for f in request.files.getlist("documents"):
            if f and f.filename and allowed_file(f.filename):
                stored = (f"{matter_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
                          f"_{secure_filename(f.filename)}")
                f.save(UPLOAD_DIR / stored)
                conn.execute(
                    "INSERT INTO documents VALUES (null,?,?,?,?)",
                    (matter_id, stored, f.filename, now)
                )
        conn.commit()

    send_intake_notification(matter_id, client_name, email, practice_area, urgency, token)
    return redirect(url_for("status", token=token))


@app.route("/status/<token>")
def status(token):
    with get_db() as conn:
        matter = conn.execute("SELECT * FROM matters WHERE token=?", (token,)).fetchone()
        if not matter:
            abort(404)
        docs   = conn.execute("SELECT * FROM documents WHERE matter_id=? ORDER BY uploaded_at DESC", (matter["id"],)).fetchall()
        events = conn.execute("SELECT * FROM events WHERE matter_id=? ORDER BY event_time DESC", (matter["id"],)).fetchall()
    return render_template("status.html", matter=matter, docs=docs, events=events, statuses=STATUSES)


@app.route("/admin")
def admin():
    with get_db() as conn:
        matters = conn.execute("SELECT * FROM matters ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", matters=matters)


@app.route("/admin/matter/<int:matter_id>", methods=["GET", "POST"])
def admin_matter(matter_id):
    with get_db() as conn:
        matter = conn.execute("SELECT * FROM matters WHERE id=?", (matter_id,)).fetchone()
        if not matter:
            abort(404)
        if request.method == "POST":
            new_status     = request.form.get("status", matter["status"])
            internal_notes = request.form.get("internal_notes", "")
            event_note     = request.form.get("event_note", "").strip() or f"Status updated to {new_status}."
            now = datetime.utcnow().isoformat()
            conn.execute("UPDATE matters SET status=?, internal_notes=? WHERE id=?",
                         (new_status, internal_notes, matter_id))
            conn.execute("INSERT INTO events (matter_id, event_time, status, note) VALUES (?,?,?,?)",
                         (matter_id, now, new_status, event_note))
            conn.commit()
            return redirect(url_for("admin_matter", matter_id=matter_id))
        docs   = conn.execute("SELECT * FROM documents WHERE matter_id=? ORDER BY uploaded_at DESC", (matter_id,)).fetchall()
        events = conn.execute("SELECT * FROM events WHERE matter_id=? ORDER BY event_time DESC", (matter_id,)).fetchall()
    return render_template("admin_matter.html", matter=matter, docs=docs,
                           events=events, statuses=STATUSES)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(str(UPLOAD_DIR), filename)


# ── Demo data ─────────────────────────────────────────────────────────────────
@app.route("/admin/load-demo", methods=["GET", "POST"])
def load_demo():
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM matters").fetchone()[0]
        if existing > 0:
            flash("Demo data already exists.", "info")
            return redirect(url_for("admin"))
        samples = [
            ("Giulia Conti",  "giulia.conti@example.com",  "+39 02 1234567", "Studio Conti",  "Shipping / Logistics", "Critical",  "Dispute over cargo damage, port of Genova."),
            ("Marco Ferretti","marco.ferretti@example.com", "+39 06 9876543", "Ferretti SRL",  "Commercial",           "High",      "Contract review for new supplier agreement."),
            ("Sofia Marino",  "sofia.marino@example.com",  "",               "",              "Employment",           "Medium",    "Wrongful termination claim."),
        ]
        for s in samples:
            token = secrets.token_hex(8).upper()
            now   = datetime.utcnow().isoformat()
            cur   = conn.execute(
                """INSERT INTO matters
                   (created_at,token,client_name,email,phone,company,
                    practice_area,urgency,description,status,internal_notes)
                   VALUES (?,?,?,?,?,?,?,?,?,'New intake','')""",
                (now, token, *s)
            )
            conn.execute("INSERT INTO events (matter_id,event_time,status,note) VALUES (?,?,?,?)",
                         (cur.lastrowid, now, "New intake", "Matter created from intake form."))
        conn.commit()
    flash("Demo data loaded.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
