"""Appointment booking API.

Public endpoint (no JWT) — clients can book from LP.
Team notifications sent on create/confirm/cancel.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.contact import Contact
from ..models.case import Case
from ..models.event import Event
from ..services.notifications import (
    create_notification,
    notify_case_intake,
    notify_case_status_changed,
)
from ..services.calendar import (
    create_or_update_calendar_event,
    delete_calendar_event,
)

appointments_bp = Blueprint("appointments", __name__, url_prefix="/api/appointments")


VALID_APPOINTMENT_STATUSES = ["Requested", "Confirmed", "Cancelled"]


@appointments_bp.get("/")
@appointments_bp.get("")
@jwt_required()
def list_appointments():
    """List all appointments (admin only)."""
    events = (
        Event.query
        .order_by(Event.event_date.desc())
        .all()
    )
    return jsonify([e.to_dict() for e in events]), 200


@appointments_bp.post("/")
@appointments_bp.post("")
def create_appointment():
    """Public endpoint — any visitor can book an appointment.

    Required:
      - fullname (str)
      - email (str)
      - phone (str)
      - event_date (ISO format)
      - title (str) — reason for appointment

    Optional:
      - caseid (int) — link to existing case
      - description (str)
      - location (str)
      - gdpr_consent (bool)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    fullname = (data.get("fullname") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    event_date_raw = (data.get("event_date") or "").strip()
    title = (data.get("title") or "").strip()

    if not fullname or not email or not event_date_raw or not title:
        return jsonify({"error": "fullname, email, event_date, and title are required"}), 400

    # Parse date
    try:
        event_date = datetime.fromisoformat(event_date_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "event_date must be ISO format (e.g. 2026-08-15T10:00:00)"}), 400

    # GDPR consent required
    if not data.get("gdpr_consent"):
        return jsonify({"error": "GDPR consent is required"}), 400

    # Create or find contact
    existing_contact = Contact.query.filter_by(email=email).first()
    if existing_contact:
        contact = existing_contact
    else:
        contact = Contact(
            fullname=fullname,
            email=email,
            phone=phone or None,
            source=data.get("source", "appointment"),
            gdpr_consent=True,
            gdpr_consent_ts=datetime.utcnow(),
        )
        db.session.add(contact)
        db.session.flush()

    # Create calendar event
    case_id = data.get("caseid")
    if case_id:
        case = Case.query.get(case_id)
    else:
        case = None

    description = (data.get("description") or "").strip() or None
    location = (data.get("location") or "").strip() or None

    event = Event(
        title=title,
        description=description,
        event_date=event_date,
        event_type="appointment",
        location=location,
    )
    db.session.add(event)
    db.session.flush()

    # Commit everything
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to create appointment"}), 500

    # ── Sync to Google Calendar (non-blocking; mock until credentials set) ──
    try:
        cal_result = create_or_update_calendar_event(
            title=title,
            description=f"{description or ''} — Richiesto da {fullname} ({email})",
            due_date=event_date,
            event_type="appointment",
            location=location or "Telefono",
        )
        if cal_result.get("event_id") and not cal_result.get("mock"):
            event.google_event_id = cal_result["event_id"]
            db.session.commit()
    except Exception:
        db.session.rollback()  # calendar sync must never break the booking

    # Notify team
    try:
        create_notification(
            user_to=None,  # broadcast
            type="appointment_requested",
            reference_type="event",
            reference_id=event.id,
            title=f"New appointment: {title}",
            body=f"Requested by {fullname} ({email}) — {event_date.isoformat()}",
        )
    except Exception:
        pass

    return jsonify({
        "contact": contact.to_dict(),
        "event": event.to_dict(),
    }), 201


@appointments_bp.patch("/<int:event_id>/confirm")
@jwt_required()
def confirm_appointment(event_id):
    """Confirm an appointment (admin only)."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    event.event_type = "confirmed_appointment"

    # Notify in-app
    try:
        create_notification(
            user_to=None,
            type="appointment_confirmed",
            reference_type="event",
            reference_id=event.id,
            title=f"Appointment confirmed: {event.title}",
            body=f"{event.event_date.isoformat()} — Client will receive confirmation",
        )
    except Exception:
        pass

    db.session.commit()
    return jsonify(event.to_dict()), 200


@appointments_bp.patch("/<int:event_id>/cancel")
@jwt_required()
def cancel_appointment(event_id):
    """Cancel an appointment (admin only)."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    old_type = event.event_type
    event.event_type = "cancelled_appointment"

    # Remove from Google Calendar if it was synced
    if event.google_event_id:
        try:
            delete_calendar_event(event.google_event_id)
        except Exception:
            pass
        event.google_event_id = None

    # Notify
    try:
        create_notification(
            user_to=None,
            type="appointment_cancelled",
            reference_type="event",
            reference_id=event.id,
            title=f"Appointment cancelled: {event.title}",
            body="Client will be notified.",
        )
    except Exception:
        pass

    db.session.commit()
    return jsonify(event.to_dict()), 200
