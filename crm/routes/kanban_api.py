"""Kanban board API — Notion-style drag & drop.

Public endpoints for the CRM Kanban view.
All endpoints require JWT authentication except health.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from ..extensions import db
from ..models.case import Case
from ..models.contact import Contact
from ..models.notification import Notification
from ..services.notifications import notify_case_status_changed

kanban_api_bp = Blueprint("kanban_api", __name__, url_prefix="/api/kanban")

VALID_CASE_STATUSES = ["New", "Reviewing", "Active", "Awaiting Client", "Closed"]


@kanban_api_bp.get("/cases")
@jwt_required()
def get_kanban_cases():
    """Return all cases grouped by status for the Kanban board."""
    cases = Case.query.order_by(Case.id.desc()).all()
    grouped = {s: [] for s in VALID_CASE_STATUSES}
    
    for c in cases:
        status = c.status if c.status in VALID_CASE_STATUSES else "New"
        # Enrich with contact info
        contact = Contact.query.get(c.contactid) if c.contactid else None
        card = c.to_dict()
        card["contact_name"] = contact.fullname if contact else "Unknown"
        card["contact_email"] = contact.email if contact else ""
        card["contact_phone"] = contact.phone if contact else ""
        grouped[status].append(card)
    
    return jsonify({"columns": grouped, "statuses": VALID_CASE_STATUSES}), 200


@kanban_api_bp.get("/stats")
@jwt_required()
def get_kanban_stats():
    """Return board statistics."""
    total = Case.query.count()
    by_status = {}
    for s in VALID_CASE_STATUSES:
        count = Case.query.filter_by(status=s).count()
        by_status[s] = count
    
    # Recent cases (last 7 days)
    week_ago = (datetime.utcnow().date()).isoformat()
    recent = Case.query.filter(Case.openedat >= week_ago).count()
    
    # Urgent cases
    urgent = Case.query.filter_by(priority="urgent").count()
    
    return jsonify({
        "total": total,
        "by_status": by_status,
        "recent_this_week": recent,
        "urgent_count": urgent,
    }), 200


@kanban_api_bp.put("/cases/<int:case_id>/status")
@jwt_required()
def update_case_status(case_id):
    """Move a case to a new column (drag & drop).
    
    This is the endpoint called when a card is dragged to a different column.
    """
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "status is required"}), 400
    
    new_status = data["status"]
    if new_status not in VALID_CASE_STATUSES:
        return jsonify({"error": f"Invalid status: {new_status}"}), 400
    
    old_status = case.status
    case.status = new_status
    db.session.commit()
    
    # Trigger notification
    try:
        contact = Contact.query.get(case.contactid) if case.contactid else None
        if contact:
            notify_case_status_changed(contact, case, old_status, new_status)
    except Exception:
        pass  # notification failure must not block the update
    
    return jsonify(case.to_dict()), 200


@kanban_api_bp.put("/cases/<int:case_id>/priority")
@jwt_required()
def update_case_priority(case_id):
    """Update case priority."""
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    
    data = request.get_json()
    if not data or "priority" not in data:
        return jsonify({"error": "priority is required"}), 400
    
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if data["priority"] not in valid_priorities:
        return jsonify({"error": f"Invalid priority: {data['priority']}"}), 400
    
    case.priority = data["priority"]
    db.session.commit()
    
    return jsonify(case.to_dict()), 200


@kanban_api_bp.get("/notifications")
@jwt_required()
def get_notifications():
    """Get notifications for the current user."""
    user_id = get_jwt_identity()
    
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    
    notifications = Notification.query.filter_by(user_to=user_id)\
        .order_by(Notification.id.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [n.to_dict() for n in notifications.items],
        "page": page,
        "per_page": per_page,
        "total": notifications.total,
        "pages": notifications.pages,
    }), 200


@kanban_api_bp.post("/notifications/<int:notif_id>/read")
@jwt_required()
def mark_notification_read(notif_id):
    """Mark a single notification as read."""
    notification = Notification.query.get(notif_id)
    if not notification:
        return jsonify({"error": "Notification not found"}), 404
    
    notification.read = True
    db.session.commit()
    
    return jsonify({"message": "Notification marked as read"}), 200


@kanban_api_bp.post("/notifications/read-all")
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications for current user as read."""
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_to=user_id, read=False).update(
        {Notification.read: True}, synchronize_session="fetch"
    )
    db.session.commit()
    
    return jsonify({"message": "All notifications marked as read"}), 200
