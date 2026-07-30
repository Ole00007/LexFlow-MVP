import os
import sqlite3
from pathlib import Path
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pagliano.db"

ALLOWED_EXT = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "txt"}
PRACTICE_AREAS = [
    "Diritto di Famiglia",
    "Recupero Crediti",
    "Esecuzioni Immobiliari",
    "Responsabilità Civile",
    "Diritto Immobiliare",
    "Contrattualistica",
    "Altro",
]

VALID_STATUSES = [
    "New intake",
    "Reviewing",
    "Active",
    "Awaiting Client",
    "Closed",
]

VALID_PRIORITIES = ["low", "medium", "high", "urgent"]

# ── Flask-SQLAlchemy DB instance ────────────────────────────────────────────
db = SQLAlchemy()


class Contact(db.Model):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    fullname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    source = Column(String(20), nullable=False, default="lp-form")
    gdpr_consent = Column(Boolean, nullable=False, default=False)
    gdpr_consent_ts = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    cases = db.relationship("Case", backref="contact", lazy=True, passive_deletes=True)

    def to_dict(self):
        return {
            "id": self.id,
            "fullname": self.fullname,
            "email": self.email,
            "phone": self.phone,
            "source": self.source,
            "gdpr_consent": self.gdpr_consent,
            "gdpr_consent_ts": self.gdpr_consent_ts.isoformat() if bool(self.gdpr_consent_ts) else None,
            "created_at": self.created_at.isoformat() if bool(self.created_at) else None,
        }


class Case(db.Model):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    practice_area = Column(String(100), nullable=False)
    urgency = Column(String(20), nullable=False, default="medium")
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="New intake")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "practice_area": self.practice_area,
            "urgency": self.urgency,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
