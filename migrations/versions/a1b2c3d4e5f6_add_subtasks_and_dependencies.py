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
    # Add parent_task_id (self-referential FK for subtask hierarchy)
    op.add_column('tasks', sa.Column('parent_task_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_tasks_parent_task_id',
        'tasks', 'tasks',
        ['parent_task_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add depends_on JSON column (array of task IDs)
    op.add_column('tasks', sa.Column('depends_on', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('tasks', 'depends_on')
    op.drop_constraint('fk_tasks_parent_task_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'parent_task_id')
