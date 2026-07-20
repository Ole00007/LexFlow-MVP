from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.notification import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.get('/')
@jwt_required()
def list_notifications():
    """List current user's notifications, newest first. Paginated."""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    paginated = Notification.get_for_user(user_id=user_id, page=page, per_page=per_page)

    return jsonify({
        'items': [n.to_dict() for n in paginated.items],
        'page': page,
        'per_page': per_page,
        'total': paginated.total,
        'pages': paginated.pages,
    }), 200


@notifications_bp.get('/unread-count')
@jwt_required()
def unread_count():
    """Return the count of unread notifications for the current user."""
    user_id = get_jwt_identity()
    count = Notification.get_unread_count(user_id)
    return jsonify({'count': count}), 200


@notifications_bp.patch('/<int:notif_id>/read')
@jwt_required()
def mark_read(notif_id):
    """Mark a single notification as read. Must belong to the current user."""
    user_id = get_jwt_identity()
    notif = Notification.query.get(notif_id)

    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    if notif.user_to != user_id:
        return jsonify({'error': 'Notification not found'}), 404

    notif.read = True
    db.session.commit()
    return jsonify(notif.to_dict()), 200


@notifications_bp.patch('/mark-all-read')
@jwt_required()
def mark_all_read():
    """Mark all of the current user's unread notifications as read."""
    user_id = get_jwt_identity()
    updated = Notification.mark_all_read(user_id)
    db.session.commit()
    return jsonify({'updated': updated}), 200
