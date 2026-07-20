from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.task import Task
from ..models.case import Case
from ..models.user import User
from datetime import datetime
import csv
import io

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
        actual_duration_minutes=data.get('actual_duration_minutes')
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict()), 201


@tasks_bp.put('/<int:task_id>')
@jwt_required()
def update_task(task_id):
    """Update an existing task."""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        status = data['status'].lower()
        if status not in VALID_STATUSES:
            return jsonify({'error': f'status must be one of {VALID_STATUSES}'}), 400
        task.status = status
    if 'priority' in data:
        priority = data['priority'].lower()
        if priority not in VALID_PRIORITIES:
            return jsonify({'error': f'priority must be one of {VALID_PRIORITIES}'}), 400
        task.priority = priority
    if 'duedate' in data:
        task.duedate = data['duedate']
    if 'eventid' in data:
        task.eventid = data['eventid']
    if 'duration_minutes' in data:
        task.duration_minutes = data['duration_minutes']
    if 'actual_duration_minutes' in data:
        task.actual_duration_minutes = data['actual_duration_minutes']
    if 'userid' in data:
        if data['userid'] is not None:
            user = User.query.get(data['userid'])
            if not user:
                return jsonify({'error': 'User not found'}), 404
        task.userid = data['userid']
    if 'assigned_to' in data:
        if data['assigned_to'] is not None:
            assigned_user = User.query.get(data['assigned_to'])
            if not assigned_user:
                return jsonify({'error': 'assigned_to user not found'}), 404
        task.assigned_to = data['assigned_to']
    
    db.session.commit()
    
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
    
    db.session.delete(task)
    db.session.commit()
    
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
