"""Fix events.id auto-increment on PostgreSQL.

The SQLite-era migration 9c2d3e4f5a6b created events with
`id INTEGER NOT NULL PRIMARY KEY`, which auto-increments on SQLite but NOT
on PostgreSQL. Booking an appointment on prod therefore failed with
"null value in column id of relation events violates not-null constraint".

This migration backfills a sequence-backed default on PostgreSQL only
(no-op on SQLite, where INTEGER PRIMARY KEY already auto-increments).
"""

from alembic import op

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6g7h8'


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            CREATE SEQUENCE IF NOT EXISTS events_id_seq;
            ALTER TABLE events ALTER COLUMN id SET DEFAULT nextval('events_id_seq');
            ALTER SEQUENCE events_id_seq OWNED BY events.id;
            SELECT setval('events_id_seq', COALESCE(MAX(id), 1)) FROM events;
        """)


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE events ALTER COLUMN id DROP DEFAULT;")
        op.execute("DROP SEQUENCE IF EXISTS events_id_seq;")
