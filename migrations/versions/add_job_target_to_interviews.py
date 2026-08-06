"""add job_target_id column to interviews

Revision ID: add_job_target_to_interviews
Revises: add_job_requirements_cascade
Create Date: 2026-08-05

The Interview model declares a job_target_id column, and interview creation
sets it, but the column was never added to the DB (the standalone SQL
migrations/add_job_target_to_interviews.sql was never applied). Add the column
with an FK that ON DELETE SET NULL so deleting a job target nulls the interview
reference instead of raising a FK violation.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_job_target_to_interviews'
down_revision = 'add_job_requirements_cascade'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('interviews', sa.Column('job_target_id', sa.String(length=64), nullable=True))
    op.create_foreign_key(
        'fk_interviews_job_target',
        'interviews',
        'job_targets',
        ['job_target_id'],
        ['job_target_id'],
        ondelete='SET NULL',
    )
    op.create_index('idx_interviews_job_target_id', 'interviews', ['job_target_id'])


def downgrade() -> None:
    op.drop_index('idx_interviews_job_target_id', table_name='interviews')
    op.drop_constraint('fk_interviews_job_target', 'interviews', type_='foreignkey')
    op.drop_column('interviews', 'job_target_id')
