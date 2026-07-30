"""Add subtasks and dependencies

Revision ID: a1b2c3d4e5f6
Revises: 9c2d3e4f5a6b
Create Date: 2026-07-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9c2d3e4f5a6b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_task_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('depends_on', sa.JSON(), nullable=True))
        # SQLite batch mode cannot add FK constraints via create_foreign_key.
        # The ORM relationship is handled by the model definition.


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_column('depends_on')
        batch_op.drop_column('parent_task_id')
