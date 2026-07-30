from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.contact import Contact
from datetime import datetime

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.get('/contacts')
def get_contacts():
    contacts = Contact.query.filter_by(is_deleted=False).order_by(Contact.id.desc()).all()
    return jsonify([c.to_dict() for c in contacts]), 200

@contacts_bp.post('/contacts')
def create_contact():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not data.get('fullname') and not data.get('full_name'):
        return jsonify({'error': 'fullname is required'}), 400

    contact = Contact(
        ownerid=data.get('ownerid'),
        fullname=data.get('fullname') or data.get('full_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        company=data.get('company'),
        source=data.get('source', 'manual'),
        gdpr_consent=bool(data.get('gdpr_consent', False)),
        gdpr_consent_ts=datetime.utcnow() if data.get('gdpr_consent') else None,
        status=data.get('status', 'lead'),
        notes=data.get('notes')
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict()), 201

@contacts_bp.delete('/contacts/<int:contact_id>')
def delete_contact(contact_id):
    contact = Contact.query.get(contact_id)
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    if contact.is_deleted:
        return jsonify({'deleted': False, 'message': 'Contact already deleted'}), 200

    contact.is_deleted = True
    contact.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'deleted': True}), 200
