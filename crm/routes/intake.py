"""Public intake endpoint — creates Contact + Case atomically from LP forms or chatbots.

No JWT required — this is a public-facing endpoint.
GDPR consent is validated before any record is created.
Triggers in-app notification to the team.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models.contact import Contact
from ..models.case import Case
from ..services.notifications import notify_case_intake

intake_bp = Blueprint("intake", __name__)


VALID_CASAREAS = [
    "diritto_di_famiglia",
    "recupero_crediti",
    "esecuzioni_immobiliari",
    "responsabilità_civile",
    "diritto_immobiliare",
    "contrattualistica",
    "altro",
]

VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
VALID_STATUSES = ["New intake", "Reviewing", "Active", "Awaiting Client", "Closed"]


@intake_bp.post("/")
@intake_bp.post("")
def create_intake():
    """Public intake endpoint.

    Accepts JSON or form data. Required fields:
      - fullname (str)
      - email (str)
      - gdpr_consent (true / "1" / checkbox value)

    Optional:
      - phone (str)
      - company (str)
      - source (str) — defaults to "manual"
      - casetype (str) — practice area / case type
      - urgency (str) — maps to case priority
      - description (str)
    """
    # ── Parse payload (JSON or form) ──────────────────────────────────────
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = {
            "fullname": request.form.get("fullname", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "company": request.form.get("company", "").strip(),
            "source": request.form.get("source", "").strip(),
            # Accept both "casetype" (CRM convention) and "practice_area" (LP form convention)
            "casetype": (request.form.get("casetype") or request.form.get("practice_area", "")).strip(),
            "urgency": request.form.get("urgency", "medium").strip().lower(),
            # Accept both "description" (CRM convention) and "message" (LP form convention)
            "description": (request.form.get("description") or request.form.get("message", "")).strip(),
            "gdpr_consent": request.form.get("gdpr_consent"),
        }

    # ── Validate required fields ─────────────────────────────────────────
    fullname = (data.get("fullname") or "").strip()
    email = (data.get("email") or "").strip()
    gdpr_raw = data.get("gdpr_consent")

    if not fullname or not email:
        return jsonify({"error": "fullname and email are required"}), 400

    # GDPR consent must be true (accept boolean, string "true"/"1"/"on")
    gdpr_truthy = {True, "true", "1", "on", "True"}
    if str(gdpr_raw).strip().lower() not in gdpr_truthy:
        return jsonify({"error": "GDPR consent is required"}), 400

    # ── Create Contact ───────────────────────────────────────────────────
    now = datetime.utcnow()
    contact = Contact(
        fullname=fullname,
        email=email,
        phone=(data.get("phone") or "").strip() or None,
        company=(data.get("company") or "").strip() or None,
        source=(data.get("source") or "manual").strip(),
        gdpr_consent=True,
        gdpr_consent_ts=now,
    )
    db.session.add(contact)
    db.session.flush()  # gives us contact.id without committing

    # ── Create Case (if casetype provided) ────────────────────────────────
    casetype_raw = (data.get("casetype") or "").strip()
    case = None
    if casetype_raw:
        urgency = (data.get("urgency") or "medium").strip().lower()
        if urgency not in VALID_PRIORITIES:
            urgency = "medium"
        description = (data.get("description") or "").strip() or None

        # Map casetype to a display-friendly label
        casemap = {
            "diritto di famiglia": "Diritto di Famiglia",
            "recupero crediti": "Recupero Crediti",
            "esecuzioni": "Esecuzioni Immobiliari",
            "responsabilità civile": "Responsabilità Civile",
            "diritto immobiliare": "Diritto Immobiliare",
            "contrattualistica": "Contrattualistica",
            "altro": "Altro",
        }
        practice_area = casemap.get(casetype_raw.lower(), casetype_raw)

        case = Case(
            contactid=contact.id,
            casetype=practice_area,
            title=f"Nuova pratica — {practice_area}" if practice_area else f"Nuova pratica — {fullname}",
            priority=urgency,
            status="New intake",
        )
        db.session.add(case)

    # ── Commit ───────────────────────────────────────────────────────────
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to create intake record"}), 500

    # ── Notify team ──────────────────────────────────────────────────────
    try:
        notify_case_intake(contact, case)
    except Exception:
        pass  # notification failure must not block intake

    result = {"contact": contact.to_dict()}
    if case:
        result["case"] = case.to_dict()

    return jsonify(result), 201
