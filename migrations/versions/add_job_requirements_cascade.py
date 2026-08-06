"""add ON DELETE CASCADE to job_requirements FK

Revision ID: add_job_requirements_cascade
Revises: add_job_targets_description
Create Date: 2026-08-05

The account-deletion service bulk-deletes JobTarget rows with a SQL DELETE,
bypassing the ORM delete-orphan cascade. The FK from job_requirements to
job_targets had no DB-level ON DELETE CASCADE, so deleting a target that
still has requirement rows raises a PostgreSQL FK violation. Add the DB-level
cascade so bulk deletes are safe.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_job_requirements_cascade'
down_revision = 'add_job_targets_description'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('job_requirements_job_target_id_fkey', 'job_requirements', type_='foreignkey')
    op.create_foreign_key(
        'job_requirements_job_target_id_fkey',
        'job_requirements',
        'job_targets',
        ['job_target_id'],
        ['job_target_id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('job_requirements_job_target_id_fkey', 'job_requirements', type_='foreignkey')
    op.create_foreign_key(
        'job_requirements_job_target_id_fkey',
        'job_requirements',
        'job_targets',
        ['job_target_id'],
        ['job_target_id'],
    )
