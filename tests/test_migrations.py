"""Tests for database migrations.

M2.6: Tests Phase 1 to Phase 2 migration structure and integrity.
"""

import pytest
import re
from pathlib import Path


class TestPhase2MigrationFile:
    """Test Phase 2 migration file structure."""

    @pytest.fixture
    def migration_file_path(self):
        """Get the Phase 2 migration file path."""
        return Path("migrations/versions/ff8290d90189_add_phase2_tables.py")

    @pytest.fixture
    def migration_content(self, migration_file_path):
        """Read migration file content."""
        return migration_file_path.read_text()

    def test_migration_file_exists(self, migration_file_path):
        """Test that the Phase 2 migration file exists."""
        assert migration_file_path.exists(), "Phase 2 migration file not found"

    def test_migration_has_correct_revision(self, migration_content):
        """Test that migration has correct revision ID."""
        assert "revision: str = 'ff8290d90189'" in migration_content

    def test_migration_has_correct_down_revision(self, migration_content):
        """Test that migration points to Phase 1 as down_revision."""
        assert "down_revision: Union[str, None] = '9f27a983fe62'" in migration_content

    def test_migration_creates_all_phase2_tables(self, migration_content):
        """Test that upgrade() creates all 14 Phase 2 tables."""
        phase2_tables = [
            "competencies",
            "job_targets",
            "job_requirements",
            "claim_competency_mappings",
            "claim_requirement_mappings",
            "verification_points",
            "evidence",
            "evidence_transitions",
            "contradictions",
            "rubric_versions",
            "ability_observations",
            "ability_profiles",
            "answer_versions",
            "training_tasks",
        ]

        for table in phase2_tables:
            assert f"op.create_table('{table}'" in migration_content, \
                f"Table '{table}' not created in migration"

    def test_migration_drops_all_phase2_tables(self, migration_content):
        """Test that downgrade() drops all Phase 2 tables."""
        phase2_tables = [
            "competencies",
            "job_targets",
            "job_requirements",
            "claim_competency_mappings",
            "claim_requirement_mappings",
            "verification_points",
            "evidence",
            "evidence_transitions",
            "contradictions",
            "rubric_versions",
            "ability_observations",
            "ability_profiles",
            "answer_versions",
            "training_tasks",
        ]

        for table in phase2_tables:
            assert f"op.drop_table('{table}')" in migration_content, \
                f"Table '{table}' not dropped in downgrade"

    def test_competency_table_has_required_columns(self, migration_content):
        """Test competencies table has all required columns."""
        # Find competencies table section (from create_table to the next create_table or create_index)
        competencies_match = re.search(
            r"op\.create_table\('competencies',.*?(?=op\.create_(?:table|index))",
            migration_content,
            re.DOTALL
        )
        assert competencies_match, "competencies table creation not found"

        competencies_def = competencies_match.group(0)
        required_columns = [
            "competency_id",
            "code",
            "domain",
            "title",
            "description",
            "level_descriptors",
            "is_active",
            "created_at",
        ]

        for col in required_columns:
            assert f"'{col}'" in competencies_def, \
                f"Column '{col}' missing from competencies table"

    def test_verification_points_has_foreign_keys(self, migration_content):
        """Test verification_points has correct foreign keys."""
        vp_match = re.search(
            r"op\.create_table\('verification_points',.*?(?=op\.create_(?:table|index))",
            migration_content,
            re.DOTALL
        )
        assert vp_match, "verification_points table creation not found"

        vp_def = vp_match.group(0)
        assert "ForeignKeyConstraint(['claim_id'], ['resume_claims.claim_id']" in vp_def
        assert "ForeignKeyConstraint(['requirement_id'], ['job_requirements.requirement_id']" in vp_def

    def test_evidence_has_foreign_keys(self, migration_content):
        """Test evidence table has correct foreign keys."""
        evidence_match = re.search(
            r"op\.create_table\('evidence',.*?(?=op\.create_(?:table|index))",
            migration_content,
            re.DOTALL
        )
        assert evidence_match, "evidence table creation not found"

        evidence_def = evidence_match.group(0)
        assert "ForeignKeyConstraint(['verification_point_id'], ['verification_points.verification_point_id']" in evidence_def
        assert "ForeignKeyConstraint(['interview_id'], ['interviews.interview_id']" in evidence_def
        assert "ForeignKeyConstraint(['answer_id'], ['interview_answers.answer_id']" in evidence_def

    def test_ability_observations_has_indexes(self, migration_content):
        """Test ability_observations has required indexes."""
        # Check for index creation after ability_observations table
        assert "op.create_index(op.f('ix_ability_observations_interview_id')" in migration_content
        assert "op.create_index(op.f('ix_ability_observations_resume_id')" in migration_content
        assert "op.create_index(op.f('ix_ability_observations_user_id')" in migration_content
        assert "op.create_index(op.f('ix_ability_observations_competency_code')" in migration_content

    def test_training_tasks_has_all_columns(self, migration_content):
        """Test training_tasks has all required columns."""
        training_match = re.search(
            r"op\.create_table\('training_tasks',.*?(?=op\.create_index)",
            migration_content,
            re.DOTALL
        )
        assert training_match, "training_tasks table creation not found"

        training_def = training_match.group(0)
        required_columns = [
            "task_id",
            "user_id",
            "resume_id",
            "interview_id",
            "task_type",
            "title",
            "description",
            "competency_code",
            "claim_id",
            "verification_point_id",
            "completion_criteria",
            "priority",
            "estimated_effort",
            "status",
        ]

        for col in required_columns:
            assert f"'{col}'" in training_def, \
                f"Column '{col}' missing from training_tasks table"

    def test_downgrade_order_respects_dependencies(self, migration_content):
        """Test that downgrade drops tables in correct order (child before parent)."""
        # Extract downgrade function
        downgrade_match = re.search(
            r"def downgrade\(\) -> None:\s*(.*)",
            migration_content,
            re.DOTALL
        )
        assert downgrade_match, "downgrade() function not found"

        downgrade_body = downgrade_match.group(1)

        # Find positions of drop statements
        def find_drop_position(table_name):
            match = re.search(rf"op\.drop_table\('{table_name}'\)", downgrade_body)
            return match.start() if match else -1

        # Child tables should be dropped before parent tables
        # training_tasks references verification_points, so should drop first
        training_pos = find_drop_position("training_tasks")
        vp_pos = find_drop_position("verification_points")
        assert training_pos < vp_pos, \
            "training_tasks should be dropped before verification_points"

        # evidence references verification_points
        evidence_pos = find_drop_position("evidence")
        assert evidence_pos < vp_pos, \
            "evidence should be dropped before verification_points"

        # verification_points references job_requirements
        job_req_pos = find_drop_position("job_requirements")
        assert vp_pos < job_req_pos, \
            "verification_points should be dropped before job_requirements"

        # job_requirements references job_targets
        job_target_pos = find_drop_position("job_targets")
        assert job_req_pos < job_target_pos, \
            "job_requirements should be dropped before job_targets"

    def test_json_columns_use_json_type(self, migration_content):
        """Test that JSON columns use sa.JSON() type."""
        # JSON columns should use sa.JSON(), not sa.Text()
        json_columns = [
            "level_descriptors",
            "evidence_expectation",
            "reason_codes",
            "spans",
            "question_forms",
            "forms_used",
            "completion_criteria",
        ]

        for col in json_columns:
            # Check that when column is defined, it uses JSON type
            # Pattern: sa.Column('column_name', sa.JSON()
            pattern = rf"sa\.Column\('{col}',\s*sa\.JSON\(\)"
            assert re.search(pattern, migration_content), \
                f"Column '{col}' should use sa.JSON() type"

    def test_indexes_dropped_before_tables(self, migration_content):
        """Test that indexes are dropped before their tables in downgrade."""
        downgrade_match = re.search(
            r"def downgrade\(\) -> None:\s*(.*)",
            migration_content,
            re.DOTALL
        )
        downgrade_body = downgrade_match.group(1)

        # Find drop_index for ability_observations
        index_drop = re.search(
            r"op\.drop_index\(op\.f\('ix_ability_observations_interview_id'\)",
            downgrade_body
        )
        table_drop = re.search(
            r"op\.drop_table\('ability_observations'\)",
            downgrade_body
        )

        assert index_drop and table_drop, \
            "ability_observations index and table drops not found"
        assert index_drop.start() < table_drop.start(), \
            "Indexes should be dropped before tables"

    def test_no_phase1_tables_modified(self, migration_content):
        """Test that migration doesn't modify Phase 1 tables."""
        phase1_tables = [
            "resume_sources",
            "resume_revisions",
            "resume_blocks",
            "resume_profiles",
            "resume_claims",
            "interviews",
            "interview_questions",
            "interview_answers",
            "interview_reports",
            "llm_calls",
            "prompt_versions",
        ]

        upgrade_match = re.search(
            r"def upgrade\(\) -> None:\s*(.*?)def downgrade",
            migration_content,
            re.DOTALL
        )
        upgrade_body = upgrade_match.group(1)

        for table in phase1_tables:
            # Check for alter_table, drop_table, or drop_column on Phase 1 tables
            assert not re.search(rf"op\.alter_table\('{table}'", upgrade_body), \
                f"Migration should not alter Phase 1 table '{table}'"
            assert not re.search(rf"op\.drop_table\('{table}'", upgrade_body), \
                f"Migration should not drop Phase 1 table '{table}'"
            assert not re.search(rf"op\.drop_column\('{table}'", upgrade_body), \
                f"Migration should not drop columns from Phase 1 table '{table}'"


class TestMigrationChain:
    """Test migration chain integrity."""

    def test_migration_chain_continuity(self):
        """Test that migration chain is continuous."""
        versions_dir = Path("migrations/versions")
        migration_files = list(versions_dir.glob("*.py"))

        # Extract revisions
        revisions = {}
        for file in migration_files:
            content = file.read_text()
            revision_match = re.search(r"revision: str = '(\w+)'", content)
            down_revision_match = re.search(r"down_revision: Union\[str, None\] = (?:'(\w+)'|None)", content)

            if revision_match:
                revision = revision_match.group(1)
                down_revision = down_revision_match.group(1) if down_revision_match else None
                revisions[revision] = {
                    "file": file.name,
                    "down_revision": down_revision
                }

        # Check that Phase 2 migration points to Phase 1
        assert "ff8290d90189" in revisions
        assert revisions["ff8290d90189"]["down_revision"] == "9f27a983fe62"

        # Check that Phase 1 migration has no down_revision
        assert "9f27a983fe62" in revisions
        assert revisions["9f27a983fe62"]["down_revision"] is None


class TestMigrationDocumentation:
    """Test migration has proper documentation."""

    @pytest.fixture
    def migration_content(self):
        """Read migration file content."""
        return Path("migrations/versions/ff8290d90189_add_phase2_tables.py").read_text()

    def test_migration_has_docstring(self, migration_content):
        """Test that migration has descriptive docstring."""
        assert '"""add_phase2_tables' in migration_content
        assert "Revision ID:" in migration_content
        assert "Revises:" in migration_content
        assert "Create Date:" in migration_content

    def test_migration_has_phase_comments(self, migration_content):
        """Test that migration has phase section comments."""
        assert "# Phase 2 M2.1: Job Target & Claim Gap" in migration_content
        assert "# Phase 2 M2.2: Evidence Engine 2.0" in migration_content
        assert "# Phase 2 M2.3: Evals & Calibration" in migration_content
        assert "# Phase 2 M2.5: Cross-session Ability Profile" in migration_content

    def test_upgrade_and_downgrade_functions_exist(self, migration_content):
        """Test that both upgrade and downgrade functions are defined."""
        assert "def upgrade() -> None:" in migration_content
        assert "def downgrade() -> None:" in migration_content

    def test_downgrade_has_proper_comments(self, migration_content):
        """Test that downgrade has section comments."""
        downgrade_match = re.search(
            r"def downgrade\(\) -> None:\s*(.*)",
            migration_content,
            re.DOTALL
        )
        downgrade_body = downgrade_match.group(1)

        assert "# Drop Phase 2 M2.5 tables" in downgrade_body
        assert "# Drop Phase 2 M2.3 tables" in downgrade_body
        assert "# Drop Phase 2 M2.2 tables" in downgrade_body
        assert "# Drop Phase 2 M2.1 tables" in downgrade_body
