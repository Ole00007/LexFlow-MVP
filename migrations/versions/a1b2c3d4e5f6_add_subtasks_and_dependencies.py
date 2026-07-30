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
        batch_op.create_foreign_key(
            'fk_tasks_parent_task_id', 'tasks', 'tasks',
            ['parent_task_id'], ['id'], 'SET NULL'
        )
        batch_op.add_column(sa.Column('depends_on', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('tasks', 'depends_on')
    op.drop_constraint('fk_tasks_parent_task_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'parent_task_id')
