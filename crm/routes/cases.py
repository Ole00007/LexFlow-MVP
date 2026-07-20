from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.case import Case
from ..models.contact import Contact
from ..models.user import User
from datetime import date, datetime

cases_bp = Blueprint("cases", __name__, url_prefix="/api")

VALID_CASE_STATUSES = ["Intake", "Review", "Closed"]
VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent']


@cases_bp.get("/cases")
@jwt_required()
def get_cases():
    """List all cases with optional pagination & filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = Case.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority.lower())
    
    paginated = query.order_by(Case.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [c.to_dict() for c in paginated.items],
        'page': page,
        'per_page': per_page,
        'total': paginated.total,
        'pages': paginated.pages
    }), 200


@cases_bp.get("/cases/<int:case_id>")
@jwt_required()
def get_case(case_id):
    """Get a single case by ID."""
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(case.to_dict()), 200


@cases_bp.post("/cases")
@jwt_required()
def create_case():
    """Create a new case."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if not data.get("contactid"):
        return jsonify({"error": "contactid is required"}), 400
    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400

    contact = Contact.query.get(data.get("contactid"))
    if not contact:
        return jsonify({"error": "contact not found"}), 404
    
    # Validate assignedto if provided
    if data.get("assignedto"):
        user = User.query.get(data.get("assignedto"))
        if not user:
            return jsonify({"error": "assignedto user not found"}), 404
    
    # Validate priority
    priority = data.get("priority", "medium").lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    
    # Validate status
    status = data.get("status", "Intake")
    if status not in VALID_CASE_STATUSES:
        status = "Intake"
    
    case = Case(
        contactid=data.get("contactid"),
        ownerid=data.get("ownerid"),
        title=data.get("title"),
        casetype=data.get("casetype"),
        status=status,
        priority=priority,
        openedat=date.fromisoformat(data["openedat"]) if data.get("openedat") else date.today(),
        duedate=date.fromisoformat(data["duedate"]) if data.get("duedate") else None,
        assignedto=data.get("assignedto"),
        eventid=data.get("eventid")
    )
    db.session.add(case)
    db.session.commit()
    return jsonify(case.to_dict()), 201


@cases_bp.put("/cases/<int:case_id>")
@jwt_required()
def update_case(case_id):
    """Update a case."""
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    
    data = request.get_json()
    
    if "title" in data:
        case.title = data["title"]
    if "casetype" in data:
        case.casetype = data["casetype"]
    if "status" in data:
        status = data["status"]
        if status in VALID_CASE_STATUSES:
            case.status = status
    if "priority" in data:
        priority = data["priority"].lower()
        if priority in VALID_PRIORITIES:
            case.priority = priority
    if "duedate" in data:
        if data["duedate"]:
            case.duedate = date.fromisoformat(data["duedate"])
        else:
            case.duedate = None
    if "assignedto" in data:
        if data["assignedto"] is not None:
            user = User.query.get(data["assignedto"])
            if not user:
                return jsonify({"error": "assignedto user not found"}), 404
        case.assignedto = data["assignedto"]
    if "eventid" in data:
        case.eventid = data["eventid"]
    
    db.session.commit()
    return jsonify(case.to_dict()), 200


@cases_bp.delete("/cases/<int:case_id>")
@jwt_required()
def delete_case(case_id):
    """Delete a case."""
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    db.session.delete(case)
    db.session.commit()
    return jsonify({"message": "Case deleted"}), 200
