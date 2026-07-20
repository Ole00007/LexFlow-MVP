"""Add task management gaps: priority, assigned_to, duration, event_id, and Event model

Revision ID: 9c2d3e4f5a6b
Revises: 8b1c2d3e4f5a
Create Date: 2026-07-20 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c2d3e4f5a6b'
down_revision = '8b1c2d3e4f5a'
branch_labels = None
depends_on = None


def upgrade():
    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('google_event_id', sa.String(255), nullable=True),
        sa.Column('createdat', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updatedat', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_event_id')
    )
    
    # Add columns to tasks table
    op.add_column('tasks', sa.Column('assigned_to', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('eventid', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('actual_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Change priority default from 'Medium' to 'medium'
    op.alter_column('tasks', 'priority', existing_type=sa.String(20), existing_default='Medium', new_default='medium')
    
    # Add foreign key for assigned_to
    op.create_foreign_key('fk_tasks_assigned_to_users', 'tasks', 'users', ['assigned_to'], ['id'], ondelete='SET NULL')
    
    # Add foreign key for eventid
    op.create_foreign_key('fk_tasks_eventid_events', 'tasks', 'events', ['eventid'], ['id'], ondelete='SET NULL')
    
    # Add columns to cases table
    op.add_column('cases', sa.Column('eventid', sa.Integer(), nullable=True))
    
    # Change priority default from 'Medium' to 'medium'
    op.alter_column('cases', 'priority', existing_type=sa.String(20), existing_default='Medium', new_default='medium')
    
    # Add foreign key for eventid in cases
    op.create_foreign_key('fk_cases_eventid_events', 'cases', 'events', ['eventid'], ['id'], ondelete='SET NULL')


def downgrade():
    # Drop foreign keys
    op.drop_constraint('fk_cases_eventid_events', 'cases')
    op.drop_constraint('fk_tasks_eventid_events', 'tasks')
    op.drop_constraint('fk_tasks_assigned_to_users', 'tasks')
    
    # Remove columns from cases
    op.drop_column('cases', 'eventid')
    op.alter_column('cases', 'priority', existing_type=sa.String(20), existing_default='medium', new_default='Medium')
    
    # Remove columns from tasks
    op.drop_column('tasks', 'completed_at')
    op.drop_column('tasks', 'actual_duration_minutes')
    op.drop_column('tasks', 'duration_minutes')
    op.drop_column('tasks', 'eventid')
    op.drop_column('tasks', 'assigned_to')
    op.alter_column('tasks', 'priority', existing_type=sa.String(20), existing_default='medium', new_default='Medium')
    
    # Drop events table
    op.drop_table('events')
