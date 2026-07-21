from ..extensions import db


VALID_NOTIFICATION_TYPES = [
    'task_assigned',
    'task_completed',
    'task_due',
    'task_created',
    'task_updated',
    'task_deleted',
    'task_comment',
    'case_updated',
    'mention',
    'broadcast',
]

VALID_REFERENCE_TYPES = ["task", "case", None]


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    # Nullable FK to users.id — null means this is a broadcast visible to everyone
    user_to = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    # Who generated the notification (null for system/broadcast)
    user_from = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type = db.Column(db.String(50), nullable=False, index=True)
    reference_type = db.Column(db.String(20), nullable=True, index=True)  # 'task' / 'case' / null
    reference_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships (optional, for convenience joins)
    recipient = db.relationship(
        "User",
        foreign_keys=[user_to],
        backref=db.backref("notifications_received", lazy=True, passive_deletes=True),
    )
    sender = db.relationship(
        "User",
        foreign_keys=[user_from],
        backref=db.backref("notifications_sent", lazy=True, passive_deletes="all"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_to": self.user_to,
            "user_from": self.user_from,
            "type": self.type,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "title": self.title,
            "body": self.body,
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    # ── Class helpers ────────────────────────────────────────────────────────

    @classmethod
    def get_unread_count(cls, user_id):
        return cls.query.filter_by(user_to=user_id, read=False).count()

    @classmethod
    def get_for_user(cls, user_id, page=1, per_page=50):
        return (
            cls.query.filter_by(user_to=user_id)
            .order_by(cls.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @classmethod
    def mark_all_read(cls, user_id):
        return (
            cls.query.filter_by(user_to=user_id, read=False)
            .update({cls.read: True}, synchronize_session="fetch")
        )
