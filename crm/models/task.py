from ..extensions import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    caseid = db.Column(db.Integer, db.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    eventid = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="pending")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    duedate = db.Column(db.Date, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    actual_duration_minutes = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    # Subtasks: self-referential hierarchy
    parent_task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    # Dependencies: JSON array of task IDs this task depends on (blocking tasks)
    depends_on = db.Column(db.JSON, nullable=True)  # e.g., [1, 3, 5]
    createdat = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updatedat = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    case = db.relationship("Case", backref=db.backref("tasks", lazy=True, passive_deletes=True))
    user = db.relationship("User", foreign_keys=[userid], backref=db.backref("tasks", lazy=True, passive_deletes=True))
    assigned_user = db.relationship("User", foreign_keys=[assigned_to], backref=db.backref("assigned_tasks", lazy=True, passive_deletes=True))
    event = db.relationship("Event", backref=db.backref("tasks", lazy=True, passive_deletes=True))
    # Self-referential for subtasks
    subtasks = db.relationship("Task", backref=db.backref("parent", remote_side=[id]), lazy=True, passive_deletes=True)

    def to_dict(self):
        return {
            "id": self.id,
            "caseid": self.caseid,
            "userid": self.userid,
            "assigned_to": self.assigned_to,
            "eventid": self.eventid,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "duedate": self.duedate.isoformat() if self.duedate else None,
            "duration_minutes": self.duration_minutes,
            "actual_duration_minutes": self.actual_duration_minutes,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_task_id": self.parent_task_id,
            "subtask_ids": [st.id for st in self.subtasks] if self.subtasks else [],
            "depends_on": self.depends_on or [],
            "createdat": self.createdat.isoformat() if self.createdat else None,
            "updatedat": self.updatedat.isoformat() if self.updatedat else None
        }
