"""add job_target_id and target_role columns to resumes

Revision ID: add_job_target_to_resumes
Revises: add_job_target_to_interviews
Create Date: 2026-08-07

Bind a resume to an optional job target so claim extraction can rank claims by
role relevance. job_target_id ON DELETE SET NULL keeps the binding intact when
the job target is deleted; target_role is a denormalized snapshot of the role
name (job target title or free text).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_job_target_to_resumes'
down_revision = 'add_job_target_to_interviews'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resume_sources', sa.Column('job_target_id', sa.String(length=64), nullable=True))
    op.add_column('resume_sources', sa.Column('target_role', sa.String(length=256), nullable=True))
    op.create_foreign_key(
        'fk_resume_sources_job_target',
        'resume_sources',
        'job_targets',
        ['job_target_id'],
        ['job_target_id'],
        ondelete='SET NULL',
    )
    op.create_index('idx_resume_sources_job_target_id', 'resume_sources', ['job_target_id'])


def downgrade() -> None:
    op.drop_index('idx_resume_sources_job_target_id', table_name='resume_sources')
    op.drop_constraint('fk_resume_sources_job_target', 'resume_sources', type_='foreignkey')
    op.drop_column('resume_sources', 'target_role')
    op.drop_column('resume_sources', 'job_target_id')
