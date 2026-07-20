"""Notification service.

Mock-first: writes Notification rows to the DB. No SMTP / webhook / push
dispatch yet — that comes in a later pass when credentials are provided.
"""
from ..extensions import db
from ..models.notification import Notification, VALID_NOTIFICATION_TYPES
from ..models.user import User


def create_notification(user_to, type, reference_type, reference_id, title, body=None, user_from=None):
    """Create and persist a single notification.

    Returns the Notification on success, or None if validation fails.
    """
    # Validate type
    if type not in VALID_NOTIFICATION_TYPES:
        return None

    # user_to is optional (broadcast), but if provided, must exist
    if user_to is not None:
        if not User.query.get(user_to):
            return None

    # user_from, if provided, must exist
    if user_from is not None and not User.query.get(user_from):
        return None

    notif = Notification(
        user_to=user_to,
        user_from=user_from,
        type=type,
        reference_type=reference_type,
        reference_id=reference_id,
        title=title[:255] if title else None,
        body=body,
    )
    db.session.add(notif)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return None
    return notif


# ── Domain helpers — one per notification "event" we care about ─────────────

def notify_task_assigned(task, actor_id):
    """Notify the user assigned to a task that they were assigned."""
    if not task or not getattr(task, "assigned_to", None):
        return None
    actor_id = actor_id or task.userid
    return create_notification(
        user_to=task.assigned_to,
        type="task_assigned",
        reference_type="task",
        reference_id=task.id,
        title=f"You were assigned task '{task.title}'",
        body=f"Assigned by user {actor_id}" if actor_id else "System assignment",
        user_from=actor_id,
    )


def notify_task_completed(task, actor_id):
    """Notify whoever originally created/owns the task that it was completed."""
    if not task:
        return None
    target = task.userid
    # Don't notify yourself
    if target and target == actor_id:
        return None
    return create_notification(
        user_to=target,
        type="task_completed",
        reference_type="task",
        reference_id=task.id,
        title=f"Task completed: '{task.title}'",
        body=f"Completed by user {actor_id}",
        user_from=actor_id,
    )


def notify_task_due_soon(task):
    """Notify the assigned user (or creator) a task is due soon."""
    if not task:
        return None
    target = task.assigned_to or task.userid
    if not target:
        return None
    due = task.duedate
    due_str = due.isoformat() if due else "soon"
    return create_notification(
        user_to=target,
        type="task_due",
        reference_type="task",
        reference_id=task.id,
        title=f"Task due: '{task.title}'",
        body=f"Due {due_str}",
    )


def notify_task_created(task, actor_id):
    """Notify the case owner that a new task was created."""
    from ..models.case import Case
    case = Case.query.get(task.caseid) if task.caseid else None
    user_to = None
    if case:
        # Case.ownerid first (explicit owner), then assignedto, fall back to case contact owner
        user_to = case.ownerid or case.assignedto
    
    if not user_to:
        return None
    
    return create_notification(
        user_to=user_to,
        type='task_created',
        reference_type='task',
        reference_id=task.id,
        title=f'New task: {task.title}',
        body=f'{task.description or "(no description)"}',
        user_from=actor_id,
    )


def notify_task_updated(task, actor_id, fields_changed=None):
    """Notify the assigned user that a task was updated."""
    user_to = task.assigned_to
    if not user_to:
        return None
    
    # Don't notify yourself
    if user_to == actor_id:
        return None
    
    changed = ', '.join(fields_changed or []) or 'details'
    return create_notification(
        user_to=user_to,
        type='task_updated',
        reference_type='task',
        reference_id=task.id,
        title=f'Task updated: {task.title}',
        body=f'Fields changed: {changed}',
        user_from=actor_id,
    )


def notify_task_deleted(task_id, actor_id):
    """Notify the assigned user (if cached) that a task was deleted."""
    # Since the task is already deleted at this point, we'd need the user_id
    # passed in or looked up beforehand. For now, skip if no user_to provided.
    # Caller should pass task.assigned_to or cache it before deletion.
    return None  # Placeholder — bulk delete / delete routes should handle their own notify with cached user_id
