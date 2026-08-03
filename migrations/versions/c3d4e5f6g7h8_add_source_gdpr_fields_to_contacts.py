"""add source gdpr fields to contacts

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-07-30 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('contacts') as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'))
        # Quoted '0' (not bare 0): valid boolean default on both SQLite and PostgreSQL
        batch_op.add_column(sa.Column('gdpr_consent', sa.Boolean(), nullable=False, server_default=sa.text("'0'")))
        batch_op.add_column(sa.Column('gdpr_consent_ts', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        batch_op.alter_column('email', existing_type=sa.String(255), nullable=False)


def downgrade():
    with op.batch_alter_table('contacts') as batch_op:
        batch_op.drop_column('created_at')
        batch_op.drop_column('gdpr_consent_ts')
        batch_op.drop_column('gdpr_consent')
        batch_op.drop_column('source')
        batch_op.alter_column('email', existing_type=sa.String(255), nullable=True)
