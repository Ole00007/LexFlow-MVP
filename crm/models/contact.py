from ..extensions import db
from datetime import datetime


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    ownerid = db.Column(db.Integer, nullable=True)
    fullname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    source = db.Column(db.String(20), nullable=False, default="manual")
    status = db.Column(db.String(50), nullable=True, default="lead")
    notes = db.Column(db.Text, nullable=True)
    gdpr_consent = db.Column(db.Boolean, nullable=False, default=False)
    gdpr_consent_ts = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ownerid": self.ownerid,
            "fullname": self.fullname,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "source": self.source,
            "status": self.status,
            "notes": self.notes,
            "gdpr_consent": self.gdpr_consent,
            "gdpr_consent_ts": self.gdpr_consent_ts.isoformat() if bool(self.gdpr_consent_ts) else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if bool(self.created_at) else None,
        }
