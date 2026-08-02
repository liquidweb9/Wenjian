"""Tests for job target templates."""

import pytest

from app.job_target import (
    ALL_TEMPLATES,
    get_template_by_id,
    list_templates,
    get_template_ids,
)


class TestJobTargetTemplates:
    """Test job target template structure."""

    def test_all_templates_count(self):
        """Six templates are defined."""
        assert len(ALL_TEMPLATES) == 6

        # Check all expected templates exist
        template_ids = {t.template_id for t in ALL_TEMPLATES}
        expected = {
            "java_backend_mid",
            "go_backend_mid",
            "python_backend_mid",
            "ai_agent_mid",
            "rag_engineer_mid",
            "backend_intern",
        }
        assert template_ids == expected

    def test_template_ids_unique(self):
        """All template IDs are unique."""
        ids = [t.template_id for t in ALL_TEMPLATES]
        assert len(ids) == len(set(ids))

    def test_template_structure(self):
        """Each template has required fields."""
        for template in ALL_TEMPLATES:
            assert template.template_id
            assert template.title
            assert template.level in ["intern", "junior", "mid", "senior", "staff"]
            assert template.interview_round
            assert template.description
            assert len(template.requirements) > 0

    def test_requirements_structure(self):
        """Each requirement has proper structure."""
        for template in ALL_TEMPLATES:
            for req in template.requirements:
                assert req.competency_code
                assert req.title
                assert req.description
                assert 0.0 <= req.importance <= 1.0
                assert 1 <= req.expected_level <= 5
                assert len(req.evidence_expectation) > 0


class TestTemplateAccess:
    """Test template access functions."""

    def test_get_template_by_id(self):
        """Get template by ID."""
        template = get_template_by_id("java_backend_mid")

        assert template is not None
        assert template.template_id == "java_backend_mid"
        assert template.title == "Java 后端工程师"
        assert template.level == "mid"

    def test_get_template_by_id_not_found(self):
        """Return None for non-existent ID."""
        template = get_template_by_id("nonexistent")
        assert template is None

    def test_list_templates_all(self):
        """List all templates."""
        templates = list_templates()
        assert len(templates) == 6

    def test_list_templates_by_level(self):
        """List templates filtered by level."""
        mid_templates = list_templates(level="mid")
        assert len(mid_templates) == 5
        assert all(t.level == "mid" for t in mid_templates)

        intern_templates = list_templates(level="intern")
        assert len(intern_templates) == 1
        assert intern_templates[0].template_id == "backend_intern"

    def test_get_template_ids(self):
        """Get list of all template IDs."""
        ids = get_template_ids()
        assert len(ids) == 6
        assert "java_backend_mid" in ids
        assert "ai_agent_mid" in ids


class TestSpecificTemplates:
    """Test specific template definitions."""

    def test_java_backend_template(self):
        """Java backend template is well-defined."""
        template = get_template_by_id("java_backend_mid")

        assert "Java" in template.title
        assert template.level == "mid"
        assert len(template.requirements) == 8

        # Check key competencies are included
        comp_codes = {req.competency_code for req in template.requirements}
        assert "backend.language_runtime" in comp_codes
        assert "backend.api_protocol" in comp_codes
        assert "backend.database_modeling" in comp_codes
        assert "backend.cache" in comp_codes

        # Check importance values are reasonable
        for req in template.requirements:
            assert 0.6 <= req.importance <= 1.0

    def test_ai_agent_template(self):
        """AI agent template is well-defined."""
        template = get_template_by_id("ai_agent_mid")

        assert "AI Agent" in template.title or "Agent" in template.title
        assert template.level == "mid"
        assert len(template.requirements) >= 5

        # Check agent-specific competencies
        comp_codes = {req.competency_code for req in template.requirements}
        assert "agent.prompt_design" in comp_codes
        assert "agent.structured_output" in comp_codes
        assert "agent.workflow_orchestration" in comp_codes

        # Prompt design should be high importance
        prompt_req = next(r for r in template.requirements if r.competency_code == "agent.prompt_design")
        assert prompt_req.importance >= 0.9

    def test_backend_intern_template(self):
        """Backend intern template has appropriate expectations."""
        template = get_template_by_id("backend_intern")

        assert template.level == "intern"
        assert template.interview_round == "resume"

        # Intern template should have lower expected levels
        for req in template.requirements:
            assert req.expected_level <= 2  # Max L2 for interns

        # Should cover basics
        comp_codes = {req.competency_code for req in template.requirements}
        assert "backend.language_runtime" in comp_codes
        assert "backend.database_modeling" in comp_codes

    def test_rag_engineer_template(self):
        """RAG engineer template focuses on RAG competencies."""
        template = get_template_by_id("rag_engineer_mid")

        comp_codes = {req.competency_code for req in template.requirements}
        assert "agent.rag_fundamentals" in comp_codes
        assert "agent.prompt_design" in comp_codes
        assert "backend.database_modeling" in comp_codes  # For vector DB

        # RAG fundamentals should be highest importance
        rag_req = next(r for r in template.requirements if r.competency_code == "agent.rag_fundamentals")
        assert rag_req.importance >= 0.9

    def test_go_backend_template(self):
        """Go backend template emphasizes concurrency."""
        template = get_template_by_id("go_backend_mid")

        comp_codes = {req.competency_code for req in template.requirements}
        assert "backend.language_runtime" in comp_codes
        assert "backend.concurrency" in comp_codes

        # Go language runtime should be very high importance
        lang_req = next(r for r in template.requirements if r.competency_code == "backend.language_runtime")
        assert lang_req.importance >= 0.9

        # Concurrency should also be high
        conc_req = next(r for r in template.requirements if r.competency_code == "backend.concurrency")
        assert conc_req.importance >= 0.85


class TestRequirementQuality:
    """Test quality of requirement definitions."""

    def test_evidence_expectations_meaningful(self):
        """Evidence expectations provide clear guidance."""
        for template in ALL_TEMPLATES:
            for req in template.requirements:
                assert len(req.evidence_expectation) >= 2  # At least 2 evidence points

                # Each evidence expectation should be substantial
                for evidence in req.evidence_expectation:
                    # Chinese descriptions can be more concise
                    assert len(evidence) >= 7, f"Evidence too short: {evidence}"

    def test_importance_distribution(self):
        """Importance values are well-distributed."""
        for template in ALL_TEMPLATES:
            importances = [req.importance for req in template.requirements]

            # Should have at least one high-importance requirement
            assert max(importances) >= 0.8

            # Should have variation (not all same importance)
            if len(importances) > 1:
                assert len(set(importances)) > 1

    def test_expected_level_appropriate(self):
        """Expected levels match job level."""
        # Mid-level templates should expect L2-L3
        mid_templates = list_templates(level="mid")
        for template in mid_templates:
            for req in template.requirements:
                assert 2 <= req.expected_level <= 4

        # Intern template should expect L1-L2
        intern_template = get_template_by_id("backend_intern")
        for req in intern_template.requirements:
            assert req.expected_level <= 2
