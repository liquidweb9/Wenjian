"""add description column to job_targets

Revision ID: add_job_targets_description
Revises: auth_m2_6_v1
Create Date: 2026-08-05

Job target descriptions are used by the JobTarget API models and frontend,
but the column was never added to the schema. Add it as nullable so existing
rows remain valid.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_job_targets_description'
down_revision = 'auth_m2_6_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('job_targets', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_targets', 'description')
