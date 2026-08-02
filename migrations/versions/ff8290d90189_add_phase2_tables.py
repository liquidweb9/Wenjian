"""add_phase2_tables

Revision ID: ff8290d90189
Revises: 9f27a983fe62
Create Date: 2026-07-31 00:05:26.926659
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'ff8290d90189'
down_revision: Union[str, None] = '9f27a983fe62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # Phase 2 M2.1: Job Target & Claim Gap
    # ============================================================

    # Competency catalog
    op.create_table('competencies',
        sa.Column('competency_id', sa.String(length=64), nullable=False),
        sa.Column('code', sa.String(length=128), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('level_descriptors', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('competency_id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_competencies_code'), 'competencies', ['code'], unique=True)

    # Job targets
    op.create_table('job_targets',
        sa.Column('job_target_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('company_name', sa.String(length=256), nullable=True),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('interview_round', sa.String(length=32), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('raw_jd', sa.Text(), nullable=True),
        sa.Column('parser_prompt_version', sa.String(length=32), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('job_target_id')
    )

    # Job requirements
    op.create_table('job_requirements',
        sa.Column('requirement_id', sa.String(length=64), nullable=False),
        sa.Column('job_target_id', sa.String(length=64), nullable=False),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('importance', sa.Float(), nullable=False),
        sa.Column('expected_level', sa.Integer(), nullable=False),
        sa.Column('evidence_expectation', sa.JSON(), nullable=False),
        sa.Column('source_span', sa.JSON(), nullable=True),
        sa.Column('is_user_confirmed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_target_id'], ['job_targets.job_target_id'], ),
        sa.PrimaryKeyConstraint('requirement_id')
    )

    # Claim-competency mappings
    op.create_table('claim_competency_mappings',
        sa.Column('mapping_id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('mapping_strength', sa.Float(), nullable=False),
        sa.Column('mapping_reason', sa.Text(), nullable=False),
        sa.Column('mapping_source', sa.String(length=32), nullable=False),
        sa.Column('prompt_version', sa.String(length=32), nullable=True),
        sa.Column('user_confirmed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id'], ),
        sa.PrimaryKeyConstraint('mapping_id')
    )

    # Claim-requirement mappings
    op.create_table('claim_requirement_mappings',
        sa.Column('mapping_id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('requirement_id', sa.String(length=64), nullable=False),
        sa.Column('relevance', sa.Float(), nullable=False),
        sa.Column('evidence_strength', sa.Float(), nullable=False),
        sa.Column('verification_priority', sa.Float(), nullable=False),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id'], ),
        sa.ForeignKeyConstraint(['requirement_id'], ['job_requirements.requirement_id'], ),
        sa.PrimaryKeyConstraint('mapping_id')
    )

    # ============================================================
    # Phase 2 M2.2: Evidence Engine 2.0
    # ============================================================

    # Verification points
    op.create_table('verification_points',
        sa.Column('verification_point_id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('requirement_id', sa.String(length=64), nullable=True),
        sa.Column('aspect', sa.Text(), nullable=False),
        sa.Column('expected_evidence', sa.JSON(), nullable=False),
        sa.Column('current_state', sa.String(length=50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=True),
        sa.Column('unresolved_reason_codes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id'], ),
        sa.ForeignKeyConstraint(['requirement_id'], ['job_requirements.requirement_id'], ),
        sa.PrimaryKeyConstraint('verification_point_id')
    )
    op.create_index(op.f('ix_verification_points_claim_id'), 'verification_points', ['claim_id'], unique=False)
    op.create_index(op.f('ix_verification_points_current_state'), 'verification_points', ['current_state'], unique=False)

    # Evidence
    op.create_table('evidence',
        sa.Column('evidence_id', sa.String(length=64), nullable=False),
        sa.Column('verification_point_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('answer_id', sa.String(length=64), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('spans', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('extracted_by', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['interview_answers.answer_id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.ForeignKeyConstraint(['verification_point_id'], ['verification_points.verification_point_id'], ),
        sa.PrimaryKeyConstraint('evidence_id')
    )
    op.create_index(op.f('ix_evidence_verification_point_id'), 'evidence', ['verification_point_id'], unique=False)
    op.create_index(op.f('ix_evidence_answer_id'), 'evidence', ['answer_id'], unique=False)

    # Evidence transitions
    op.create_table('evidence_transitions',
        sa.Column('transition_id', sa.String(length=64), nullable=False),
        sa.Column('verification_point_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('from_state', sa.String(length=50), nullable=False),
        sa.Column('to_state', sa.String(length=50), nullable=False),
        sa.Column('reason_code', sa.String(length=100), nullable=False),
        sa.Column('answer_id', sa.String(length=64), nullable=True),
        sa.Column('evaluation_id', sa.String(length=64), nullable=True),
        sa.Column('evidence_spans', sa.JSON(), nullable=True),
        sa.Column('policy_version', sa.String(length=20), nullable=False),
        sa.Column('prompt_version', sa.String(length=20), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['interview_answers.answer_id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.ForeignKeyConstraint(['verification_point_id'], ['verification_points.verification_point_id'], ),
        sa.PrimaryKeyConstraint('transition_id')
    )
    op.create_index(op.f('ix_evidence_transitions_verification_point_id'), 'evidence_transitions', ['verification_point_id'], unique=False)

    # Contradictions
    op.create_table('contradictions',
        sa.Column('contradiction_id', sa.String(length=64), nullable=False),
        sa.Column('verification_point_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('conflicting_answers', sa.JSON(), nullable=False),
        sa.Column('contradiction_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('clarification_question', sa.Text(), nullable=True),
        sa.Column('resolution_status', sa.String(length=50), nullable=False),
        sa.Column('resolution_answer_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.ForeignKeyConstraint(['resolution_answer_id'], ['interview_answers.answer_id'], ),
        sa.ForeignKeyConstraint(['verification_point_id'], ['verification_points.verification_point_id'], ),
        sa.PrimaryKeyConstraint('contradiction_id')
    )
    op.create_index(op.f('ix_contradictions_verification_point_id'), 'contradictions', ['verification_point_id'], unique=False)
    op.create_index(op.f('ix_contradictions_resolution_status'), 'contradictions', ['resolution_status'], unique=False)

    # ============================================================
    # Phase 2 M2.3: Evals & Calibration
    # ============================================================

    # Rubric versions
    op.create_table('rubric_versions',
        sa.Column('rubric_id', sa.String(length=64), nullable=False),
        sa.Column('rubric_name', sa.String(length=128), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('dimension_weights', sa.JSON(), nullable=False),
        sa.Column('dimension_descriptors', sa.JSON(), nullable=False),
        sa.Column('scoring_guidelines', sa.Text(), nullable=True),
        sa.Column('level_descriptors', sa.JSON(), nullable=True),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('rubric_id')
    )
    op.create_index(op.f('ix_rubric_versions_rubric_name'), 'rubric_versions', ['rubric_name'], unique=False)

    # ============================================================
    # Phase 2 M2.5: Cross-session Ability Profile
    # ============================================================

    # Ability observations
    op.create_table('ability_observations',
        sa.Column('observation_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('question_count', sa.Integer(), nullable=False),
        sa.Column('question_forms', sa.JSON(), nullable=False),
        sa.Column('avg_score', sa.Float(), nullable=False),
        sa.Column('max_depth', sa.Integer(), nullable=False),
        sa.Column('verification_points_addressed', sa.Integer(), nullable=False),
        sa.Column('verification_points_verified', sa.Integer(), nullable=False),
        sa.Column('evidence_strength', sa.Float(), nullable=False),
        sa.Column('evidence_status', sa.String(length=50), nullable=False),
        sa.Column('contradiction_count', sa.Integer(), nullable=False),
        sa.Column('dimension_scores', sa.JSON(), nullable=False),
        sa.Column('rubric_version', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.PrimaryKeyConstraint('observation_id')
    )
    op.create_index(op.f('ix_ability_observations_interview_id'), 'ability_observations', ['interview_id'], unique=False)
    op.create_index(op.f('ix_ability_observations_resume_id'), 'ability_observations', ['resume_id'], unique=False)
    op.create_index(op.f('ix_ability_observations_user_id'), 'ability_observations', ['user_id'], unique=False)
    op.create_index(op.f('ix_ability_observations_competency_code'), 'ability_observations', ['competency_code'], unique=False)

    # Ability profiles
    op.create_table('ability_profiles',
        sa.Column('profile_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('total_interviews', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('forms_used', sa.JSON(), nullable=False),
        sa.Column('avg_score', sa.Float(), nullable=False),
        sa.Column('score_trend', sa.String(length=20), nullable=True),
        sa.Column('stability', sa.String(length=20), nullable=False),
        sa.Column('stability_factors', sa.JSON(), nullable=False),
        sa.Column('transfer_status', sa.String(length=50), nullable=False),
        sa.Column('counterfactual_performance', sa.Float(), nullable=True),
        sa.Column('last_evidence_status', sa.String(length=50), nullable=False),
        sa.Column('last_verification_date', sa.DateTime(), nullable=True),
        sa.Column('unresolved_gaps', sa.JSON(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_index(op.f('ix_ability_profiles_user_id'), 'ability_profiles', ['user_id'], unique=False)
    op.create_index(op.f('ix_ability_profiles_resume_id'), 'ability_profiles', ['resume_id'], unique=False)
    op.create_index(op.f('ix_ability_profiles_competency_code'), 'ability_profiles', ['competency_code'], unique=False)

    # Answer versions
    op.create_table('answer_versions',
        sa.Column('version_id', sa.String(length=64), nullable=False),
        sa.Column('answer_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('answer_hash', sa.String(length=64), nullable=False),
        sa.Column('diff_summary', sa.JSON(), nullable=True),
        sa.Column('is_substantive_change', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['interview_answers.answer_id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['interview_questions.question_id'], ),
        sa.PrimaryKeyConstraint('version_id')
    )
    op.create_index(op.f('ix_answer_versions_answer_id'), 'answer_versions', ['answer_id'], unique=False)

    # Training tasks
    op.create_table('training_tasks',
        sa.Column('task_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('interview_id', sa.String(length=64), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('competency_code', sa.String(length=128), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=True),
        sa.Column('verification_point_id', sa.String(length=64), nullable=True),
        sa.Column('completion_criteria', sa.JSON(), nullable=False),
        sa.Column('priority', sa.Float(), nullable=False),
        sa.Column('estimated_effort', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.interview_id'], ),
        sa.ForeignKeyConstraint(['verification_point_id'], ['verification_points.verification_point_id'], ),
        sa.PrimaryKeyConstraint('task_id')
    )
    op.create_index(op.f('ix_training_tasks_user_id'), 'training_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_training_tasks_resume_id'), 'training_tasks', ['resume_id'], unique=False)
    op.create_index(op.f('ix_training_tasks_interview_id'), 'training_tasks', ['interview_id'], unique=False)


def downgrade() -> None:
    # Drop Phase 2 M2.5 tables
    op.drop_index(op.f('ix_training_tasks_interview_id'), table_name='training_tasks')
    op.drop_index(op.f('ix_training_tasks_resume_id'), table_name='training_tasks')
    op.drop_index(op.f('ix_training_tasks_user_id'), table_name='training_tasks')
    op.drop_table('training_tasks')

    op.drop_index(op.f('ix_answer_versions_answer_id'), table_name='answer_versions')
    op.drop_table('answer_versions')

    op.drop_index(op.f('ix_ability_profiles_competency_code'), table_name='ability_profiles')
    op.drop_index(op.f('ix_ability_profiles_resume_id'), table_name='ability_profiles')
    op.drop_index(op.f('ix_ability_profiles_user_id'), table_name='ability_profiles')
    op.drop_table('ability_profiles')

    op.drop_index(op.f('ix_ability_observations_competency_code'), table_name='ability_observations')
    op.drop_index(op.f('ix_ability_observations_user_id'), table_name='ability_observations')
    op.drop_index(op.f('ix_ability_observations_resume_id'), table_name='ability_observations')
    op.drop_index(op.f('ix_ability_observations_interview_id'), table_name='ability_observations')
    op.drop_table('ability_observations')

    # Drop Phase 2 M2.3 tables
    op.drop_index(op.f('ix_rubric_versions_rubric_name'), table_name='rubric_versions')
    op.drop_table('rubric_versions')

    # Drop Phase 2 M2.2 tables
    op.drop_index(op.f('ix_contradictions_resolution_status'), table_name='contradictions')
    op.drop_index(op.f('ix_contradictions_verification_point_id'), table_name='contradictions')
    op.drop_table('contradictions')

    op.drop_index(op.f('ix_evidence_transitions_verification_point_id'), table_name='evidence_transitions')
    op.drop_table('evidence_transitions')

    op.drop_index(op.f('ix_evidence_answer_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_verification_point_id'), table_name='evidence')
    op.drop_table('evidence')

    op.drop_index(op.f('ix_verification_points_current_state'), table_name='verification_points')
    op.drop_index(op.f('ix_verification_points_claim_id'), table_name='verification_points')
    op.drop_table('verification_points')

    # Drop Phase 2 M2.1 tables
    op.drop_table('claim_requirement_mappings')
    op.drop_table('claim_competency_mappings')
    op.drop_table('job_requirements')
    op.drop_table('job_targets')

    op.drop_index(op.f('ix_competencies_code'), table_name='competencies')
    op.drop_table('competencies')
