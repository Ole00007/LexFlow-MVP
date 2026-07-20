from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.task import Task
from ..models.case import Case
from ..models.user import User
from datetime import datetime
import csv
import io
from ..services.notifications import (
    notify_task_assigned,
    notify_task_completed,
    notify_task_created,
    notify_task_updated,
    notify_task_deleted,
)

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent']
VALID_STATUSES = ['pending', 'in_progress', 'completed']


@tasks_bp.get('/')
@jwt_required()
def get_tasks():
    """List all tasks with optional pagination & filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = Task.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority.lower())
    
    paginated = query.order_by(Task.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [t.to_dict() for t in paginated.items],
        'page': page,
        'per_page': per_page,
        'total': paginated.total,
        'pages': paginated.pages
    }), 200


@tasks_bp.get('/<int:task_id>')
@jwt_required()
def get_task(task_id):
    """Get a single task by ID."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task.to_dict()), 200


@tasks_bp.post('/')
@jwt_required()
def create_task():
    """Create a new task with full support for priority, assigned_to, duration fields."""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('caseid'):
        return jsonify({'error': 'title and caseid are required'}), 400
    
    # Validate case exists
    case = Case.query.get(data.get('caseid'))
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    # Validate user if provided
    if data.get('userid'):
        user = User.query.get(data.get('userid'))
        if not user:
            return jsonify({'error': 'User not found'}), 404
    
    # Validate assigned_to if provided
    if data.get('assigned_to'):
        assigned_user = User.query.get(data.get('assigned_to'))
        if not assigned_user:
            return jsonify({'error': 'assigned_to user not found'}), 404
    
    # Validate priority
    priority = data.get('priority', 'medium').lower()
    if priority not in VALID_PRIORITIES:
        return jsonify({'error': f'priority must be one of {VALID_PRIORITIES}'}), 400
    
    # Validate status
    status = data.get('status', 'pending').lower()
    if status not in VALID_STATUSES:
        return jsonify({'error': f'status must be one of {VALID_STATUSES}'}), 400
    
    task = Task(
        caseid=data.get('caseid'),
        userid=data.get('userid'),
        assigned_to=data.get('assigned_to'),
        title=data.get('title'),
        description=data.get('description'),
        status=status,
        priority=priority,
        duedate=data.get('duedate'),
        eventid=data.get('eventid'),
        duration_minutes=data.get('duration_minutes'),
        actual_duration_minutes=data.get('actual_duration_minutes'),
        parent_task_id=data.get('parent_task_id'),
        depends_on=data.get('depends_on')
    )
    
    db.session.add(task)
    db.session.commit()
    
    
    
    # In-app notifications (conditional on what changed)
    try:
        actor = get_jwt_identity()
        if 'assigned_to' in data:
            notify_task_assigned(task, actor_id=actor)
        else:
            notify_task_updated(task, actor_id=actor, fields_changed=list(data.keys()))
    except Exception:
        pass
    
    return jsonify(task.to_dict()), 200


@tasks_bp.patch('/<int:task_id>/complete')
@jwt_required()
def complete_task(task_id):
    """Mark task as completed, set actual_duration_minutes and completed_at in one call."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json() or {}
    
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    if 'actual_duration_minutes' in data:
        task.actual_duration_minutes = data['actual_duration_minutes']
    
    db.session.commit()
    
    
    
    # In-app notification
    try:
        notify_task_completed(task, actor_id=get_jwt_identity())
    except Exception:
        pass
    
    return jsonify({
        'message': 'Task marked as completed',
        'task': task.to_dict()
    }), 200


@tasks_bp.delete('/<int:task_id>')
@jwt_required()
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Capture state before deletion for notification
    task_dict = task.to_dict()
    assigned_to_before_delete = task.assigned_to
    actor_id = get_jwt_identity()
    
    db.session.delete(task)
    db.session.commit()
    
    
    # In-app notification to the previously-assigned user
    if assigned_to_before_delete and assigned_to_before_delete != actor_id:
        try:
            from ..services.notifications import create_notification
            create_notification(
                user_to=assigned_to_before_delete,
                type='task_deleted',
                reference_type='task',
                reference_id=task.id,
                title=f'Task deleted: {task_dict.get("title", "")}',
                user_from=actor_id,
            )
        except Exception:
            pass
    
    return jsonify({'message': 'Task deleted'}), 200


@tasks_bp.get('/export.csv')
@jwt_required()
def export_tasks_csv():
    """Export all tasks as CSV: title, status, priority, due_date, assigned_to, duration_minutes, event_id."""
    tasks = Task.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'caseid', 'title', 'description', 'status', 'priority', 'due_date', 'assigned_to', 'duration_minutes', 'actual_duration_minutes', 'event_id'])
    
    for task in tasks:
        writer.writerow([
            task.id,
            task.caseid,
            task.title,
            task.description or '',
            task.status,
            task.priority,
            task.duedate.isoformat() if task.duedate else '',
            task.assigned_to or '',
            task.duration_minutes or '',
            task.actual_duration_minutes or '',
            task.eventid or ''
        ])
    
    output.seek(0)
    file_stream = io.BytesIO(output.getvalue().encode())
    
    return send_file(
        file_stream,
        mimetype='text/csv',
        as_attachment=True,
        download_name='tasks_export.csv'
    )


@tasks_bp.post('/import')
@jwt_required()
def import_tasks_csv():
    """Import tasks from CSV. Required: title, caseid. Optional: all others."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV'}), 400
    
    imported_count = 0
    error_count = 0
    error_rows = []
    
    try:
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        
        for row_idx, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                # Required fields
                title = row.get('title', '').strip()
                caseid = row.get('caseid', '').strip()
                
                if not title or not caseid:
                    error_rows.append({'row': row_idx, 'error': 'title and caseid are required'})
                    error_count += 1
                    continue
                
                # Validate case
                try:
                    caseid = int(caseid)
                except ValueError:
                    error_rows.append({'row': row_idx, 'error': 'caseid must be an integer'})
                    error_count += 1
                    continue
                
                case = Case.query.get(caseid)
                if not case:
                    error_rows.append({'row': row_idx, 'error': f'Case ID {caseid} not found'})
                    error_count += 1
                    continue
                
                # Optional fields
                userid = None
                if row.get('userid', '').strip():
                    try:
                        userid = int(row['userid'])
                        user = User.query.get(userid)
                        if not user:
                            error_rows.append({'row': row_idx, 'error': f'User ID {userid} not found'})
                            error_count += 1
                            continue
                    except ValueError:
                        error_rows.append({'row': row_idx, 'error': 'userid must be an integer'})
                        error_count += 1
                        continue
                
                assigned_to = None
                if row.get('assigned_to', '').strip():
                    try:
                        assigned_to = int(row['assigned_to'])
                        assigned_user = User.query.get(assigned_to)
                        if not assigned_user:
                            error_rows.append({'row': row_idx, 'error': f'assigned_to user ID {assigned_to} not found'})
                            error_count += 1
                            continue
                    except ValueError:
                        error_rows.append({'row': row_idx, 'error': 'assigned_to must be an integer'})
                        error_count += 1
                        continue
                
                status = row.get('status', 'pending').strip().lower()
                if status not in VALID_STATUSES:
                    status = 'pending'
                
                priority = row.get('priority', 'medium').strip().lower()
                if priority not in VALID_PRIORITIES:
                    priority = 'medium'
                
                duedate = None
                if row.get('due_date', '').strip():
                    try:
                        duedate = datetime.fromisoformat(row['due_date'].strip()).date()
                    except ValueError:
                        pass  # Ignore invalid dates
                
                duration_minutes = None
                if row.get('duration_minutes', '').strip():
                    try:
                        duration_minutes = int(row['duration_minutes'])
                    except ValueError:
                        pass
                
                eventid = None
                if row.get('event_id', '').strip():
                    try:
                        eventid = int(row['event_id'])
                    except ValueError:
                        pass
                
                # Create task
                task = Task(
                    caseid=caseid,
                    userid=userid,
                    assigned_to=assigned_to,
                    title=title,
                    description=row.get('description', '').strip() or None,
                    status=status,
                    priority=priority,
                    duedate=duedate,
                    duration_minutes=duration_minutes,
                    eventid=eventid
                )
                
                db.session.add(task)
                imported_count += 1
            
            except Exception as e:
                error_rows.append({'row': row_idx, 'error': str(e)})
                error_count += 1
        
        db.session.commit()
        
        return jsonify({
            'imported': imported_count,
            'errors': error_count,
            'error_rows': error_rows
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to process CSV: {str(e)}'}), 400


# ── Bulk Operations ──────────────────────────────────────────────────────────

@tasks_bp.patch('/bulk-update')
@jwt_required()
def bulk_update_tasks():
    """Bulk update status, priority, or assigned_to for multiple tasks.
    Payload: {"task_ids": [1,2,3], "status": "in_progress", "priority": "high", "assigned_to": 5}
    Returns: {"updated": 2, "failed": 1, "errors": [...]}
    """
    data = request.get_json()
    
    if not data or not data.get('task_ids'):
        return jsonify({'error': 'task_ids array is required'}), 400
    
    task_ids = data.get('task_ids')
    if not isinstance(task_ids, list):
        return jsonify({'error': 'task_ids must be an array'}), 400
    
    updates = {}
    if 'status' in data:
        status = data['status'].lower()
        if status not in VALID_STATUSES:
            return jsonify({'error': f'status must be one of {VALID_STATUSES}'}), 400
        updates['status'] = status
    
    if 'priority' in data:
        priority = data['priority'].lower()
        if priority not in VALID_PRIORITIES:
            return jsonify({'error': f'priority must be one of {VALID_PRIORITIES}'}), 400
        updates['priority'] = priority
    
    if 'assigned_to' in data:
        assigned_user_id = data['assigned_to']
        if assigned_user_id is not None:
            user = User.query.get(assigned_user_id)
            if not user:
                return jsonify({'error': f'User ID {assigned_user_id} not found'}), 404
        updates['assigned_to'] = assigned_user_id
    
    if not updates:
        return jsonify({'error': 'At least one update field required (status, priority, assigned_to)'}), 400
    
    updated = 0
    errors = []
    
    for task_id in task_ids:
        task = Task.query.get(task_id)
        if not task:
            errors.append({'id': task_id, 'error': 'Task not found'})
            continue
        
        for field, value in updates.items():
            setattr(task, field, value)
        
        updated += 1
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({'updated': updated, 'failed': len(errors), 'errors': errors}), 200


@tasks_bp.post('/bulk-complete')
@jwt_required()
def bulk_complete_tasks():
    """Mark multiple tasks as completed.
    Payload: {"task_ids": [1,2,3], "actual_duration_minutes": 60}
    Returns: {"completed": 2, "failed": 1, "errors": [...]}
    """
    data = request.get_json() or {}
    task_ids = data.get('task_ids')
    
    if not task_ids or not isinstance(task_ids, list):
        return jsonify({'error': 'task_ids array is required'}), 400
    
    actual_duration = data.get('actual_duration_minutes')
    if actual_duration is not None:
        try:
            actual_duration = int(actual_duration)
            if actual_duration < 0:
                return jsonify({'error': 'actual_duration_minutes must be >= 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'actual_duration_minutes must be an integer'}), 400
    
    completed = 0
    errors = []
    
    for task_id in task_ids:
        task = Task.query.get(task_id)
        if not task:
            errors.append({'id': task_id, 'error': 'Task not found'})
            continue
        
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        if actual_duration is not None:
            task.actual_duration_minutes = actual_duration
        
        completed += 1
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({'completed': completed, 'failed': len(errors), 'errors': errors}), 200


@tasks_bp.delete('/bulk-delete')
@jwt_required()
def bulk_delete_tasks():
    """Delete multiple tasks.
    Payload: {"task_ids": [1,2,3]}
    Returns: {"deleted": 2, "failed": 1, "errors": [...]}
    """
    data = request.get_json()
    
    if not data or not data.get('task_ids'):
        return jsonify({'error': 'task_ids array is required'}), 400
    
    task_ids = data.get('task_ids')
    if not isinstance(task_ids, list):
        return jsonify({'error': 'task_ids must be an array'}), 400
    
    deleted = 0
    errors = []
    
    for task_id in task_ids:
        task = Task.query.get(task_id)
        if not task:
            errors.append({'id': task_id, 'error': 'Task not found'})
            continue
        
        db.session.delete(task)
        deleted += 1
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({'deleted': deleted, 'failed': len(errors), 'errors': errors}), 200
