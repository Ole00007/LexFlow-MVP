from ..extensions import db
from datetime import datetime


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(50), nullable=True)  # e.g., "court_date", "deadline", "meeting"
    location = db.Column(db.String(255), nullable=True)
    google_event_id = db.Column(db.String(255), nullable=True, unique=True)  # External Google Calendar event ID
    createdat = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedat = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_type": self.event_type,
            "location": self.location,
            "google_event_id": self.google_event_id,
            "createdat": self.createdat.isoformat() if self.createdat else None,
            "updatedat": self.updatedat.isoformat() if self.updatedat else None
        }
