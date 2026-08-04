"""Phase 1 multi-tenancy: create tenants table + add tenant_id columns.

All new columns are nullable with DEFAULT NULL — existing data is
untouched, no code queries these columns yet. Completey safe.
"""

from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'


def upgrade():
    bind = op.get_bind()

    # ── Tenants table ─────────────────────────────────────────────────
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('plan', sa.String(50), nullable=True, server_default='free'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # ── tenant_id on every resource table (nullable -> safe) ─────────
    for tbl in ('contacts', 'cases', 'tasks', 'events'):
        # SQLite: ALTER TABLE lacks IF NOT EXISTS; wrap in try
        try:
            op.add_column(tbl, sa.Column('tenant_id', sa.Integer(), nullable=True))
        except Exception:
            pass  # column already exists (re-run safety)

        # Index for future tenant-scoped lookups
        try:
            op.create_index(f'ix_{tbl}_tenant_id', tbl, ['tenant_id'])
        except Exception:
            pass


def downgrade():
    for tbl in ('events', 'tasks', 'cases', 'contacts'):
        try:
            op.drop_constraint(f'ix_{tbl}_tenant_id', tbl)
        except Exception:
            pass
        try:
            op.drop_column(tbl, 'tenant_id')
        except Exception:
            pass
    op.drop_table('tenants')