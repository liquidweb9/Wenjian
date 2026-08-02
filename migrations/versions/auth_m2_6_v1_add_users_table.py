"""add users table and ownership

Revision ID: auth_m2_6_v1
Revises: ff8290d90189
Create Date: 2026-07-31

M2.6 Task #13: Add User table and user_id foreign keys to existing tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'auth_m2_6_v1'
down_revision = 'ff8290d90189'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Add user_id columns to existing tables (nullable initially)
    op.add_column('resume_sources', sa.Column('user_id', sa.String(length=64), nullable=True))
    op.add_column('interviews', sa.Column('user_id', sa.String(length=64), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_resume_sources_user_id'), 'resume_sources', ['user_id'], unique=False)
    op.create_index(op.f('ix_interviews_user_id'), 'interviews', ['user_id'], unique=False)

    # Add foreign keys
    op.create_foreign_key('fk_resume_sources_user_id', 'resume_sources', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_interviews_user_id', 'interviews', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_job_targets_user_id', 'job_targets', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_ability_observations_user_id', 'ability_observations', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_ability_profiles_user_id', 'ability_profiles', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_training_tasks_user_id', 'training_tasks', 'users', ['user_id'], ['user_id'])

    # Note: user_id columns remain nullable for backward compatibility
    # Production deployment should:
    # 1. Create a default user account
    # 2. Update existing records to assign them to default user
    # 3. Make user_id NOT NULL in a subsequent migration


def downgrade() -> None:
    # Drop foreign keys
    op.drop_constraint('fk_training_tasks_user_id', 'training_tasks', type_='foreignkey')
    op.drop_constraint('fk_ability_profiles_user_id', 'ability_profiles', type_='foreignkey')
    op.drop_constraint('fk_ability_observations_user_id', 'ability_observations', type_='foreignkey')
    op.drop_constraint('fk_job_targets_user_id', 'job_targets', type_='foreignkey')
    op.drop_constraint('fk_interviews_user_id', 'interviews', type_='foreignkey')
    op.drop_constraint('fk_resume_sources_user_id', 'resume_sources', type_='foreignkey')

    # Drop indexes
    op.drop_index(op.f('ix_interviews_user_id'), table_name='interviews')
    op.drop_index(op.f('ix_resume_sources_user_id'), table_name='resume_sources')

    # Drop user_id columns
    op.drop_column('interviews', 'user_id')
    op.drop_column('resume_sources', 'user_id')

    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
