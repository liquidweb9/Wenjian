"""Tests for question form selector.

M2.4: Tests form selection logic for multi-form ability verification.
"""

import pytest
from app.interview.question_forms import (
    QuestionForm,
    QuestionFormSelector,
    FORM_CHARACTERISTICS,
    get_form_prompt_guidance,
)


class TestQuestionFormSelector:
    """Test question form selection logic."""

    def test_select_form_shallow_depth(self):
        """Test form selection for shallow depths (1-2)."""
        selector = QuestionFormSelector()

        # Depth 1 should prefer CONCEPT or PROJECT_DETAIL
        form = selector.select_form(
            competency_code="backend.api",
            current_depth=1,
            project_context_available=True,
            form_history=None,
        )

        assert form in [QuestionForm.CONCEPT, QuestionForm.PROJECT_DETAIL]

    def test_select_form_mid_depth(self):
        """Test form selection for mid depths (3-4)."""
        selector = QuestionFormSelector()

        # Depth 3 should prefer PROJECT_DETAIL, DESIGN_RATIONALE, or DEBUGGING
        form = selector.select_form(
            competency_code="backend.distributed",
            current_depth=3,
            project_context_available=True,
            form_history=None,
        )

        assert form in [
            QuestionForm.PROJECT_DETAIL,
            QuestionForm.DESIGN_RATIONALE,
            QuestionForm.DEBUGGING,
        ]

    def test_select_form_deep_depth(self):
        """Test form selection for deep depths (6-7)."""
        selector = QuestionFormSelector()

        # Depth 7 should prefer COUNTERFACTUAL or EVOLUTION
        form = selector.select_form(
            competency_code="backend.architecture",
            current_depth=7,
            project_context_available=True,
            form_history=None,
        )

        assert form in [QuestionForm.COUNTERFACTUAL, QuestionForm.EVOLUTION]

    def test_avoid_repetition(self):
        """Test that selector avoids recently used forms."""
        selector = QuestionFormSelector()

        # First call
        form1 = selector.select_form(
            competency_code="backend.api",
            current_depth=3,
            project_context_available=True,
            form_history=None,
        )

        # Second call with form1 in history
        form2 = selector.select_form(
            competency_code="backend.api",
            current_depth=3,
            project_context_available=True,
            form_history=[form1.value],
        )

        # Should select different form
        assert form2 != form1

    def test_no_project_context_filters_forms(self):
        """Test that forms requiring project context are filtered out."""
        selector = QuestionFormSelector()

        # Without project context, should only get CONCEPT
        form = selector.select_form(
            competency_code="backend.algorithms",
            current_depth=2,
            project_context_available=False,
            form_history=None,
        )

        # CONCEPT doesn't require project context
        assert form == QuestionForm.CONCEPT

    def test_all_forms_used_allows_repetition(self):
        """Test that selector allows repetition when all forms are used."""
        selector = QuestionFormSelector()

        # Use all forms suitable for depth 3
        all_forms = [
            QuestionForm.PROJECT_DETAIL.value,
            QuestionForm.DESIGN_RATIONALE.value,
            QuestionForm.DEBUGGING.value,
            QuestionForm.CONCEPT.value,
        ]

        # Should still return a valid form
        form = selector.select_form(
            competency_code="backend.api",
            current_depth=3,
            project_context_available=True,
            form_history=all_forms,
        )

        assert form in [
            QuestionForm.PROJECT_DETAIL,
            QuestionForm.DESIGN_RATIONALE,
            QuestionForm.DEBUGGING,
            QuestionForm.CONCEPT,
        ]

    def test_get_form_coverage(self):
        """Test form coverage calculation."""
        selector = QuestionFormSelector()

        form_history = [
            QuestionForm.CONCEPT.value,
            QuestionForm.PROJECT_DETAIL.value,
            QuestionForm.PROJECT_DETAIL.value,
            QuestionForm.DEBUGGING.value,
        ]

        coverage = selector.get_form_coverage(form_history)

        assert coverage[QuestionForm.CONCEPT.value] == 1
        assert coverage[QuestionForm.PROJECT_DETAIL.value] == 2
        assert coverage[QuestionForm.DEBUGGING.value] == 1
        assert coverage[QuestionForm.COUNTERFACTUAL.value] == 0

    def test_get_untested_abilities(self):
        """Test untested ability detection."""
        selector = QuestionFormSelector()

        # Only used CONCEPT and PROJECT_DETAIL
        form_history = [
            QuestionForm.CONCEPT.value,
            QuestionForm.PROJECT_DETAIL.value,
        ]

        untested = selector.get_untested_abilities(form_history)

        # Should have several untested abilities
        assert len(untested) > 0
        assert "problem_solving" in untested  # From DEBUGGING
        assert "transfer_ability" in untested  # From COUNTERFACTUAL

    def test_depth_range_enforcement(self):
        """Test that forms outside depth range are not selected."""
        selector = QuestionFormSelector()

        # Depth 2 should not select COUNTERFACTUAL (requires 6-7)
        form = selector.select_form(
            competency_code="backend.api",
            current_depth=2,
            project_context_available=True,
            form_history=None,
        )

        assert form != QuestionForm.COUNTERFACTUAL

    def test_form_characteristics_complete(self):
        """Test that all forms have characteristics defined."""
        for form in QuestionForm:
            assert form in FORM_CHARACTERISTICS
            chars = FORM_CHARACTERISTICS[form]

            # Check required fields
            assert "depth_range" in chars
            assert "requires_project_context" in chars
            assert "tests_ability" in chars
            assert "description" in chars

            # Validate depth range
            min_depth, max_depth = chars["depth_range"]
            assert 1 <= min_depth <= 7
            assert 1 <= max_depth <= 7
            assert min_depth <= max_depth


class TestFormPromptGuidance:
    """Test form-specific prompt guidance."""

    def test_all_forms_have_guidance(self):
        """Test that all forms have prompt guidance defined."""
        for form in QuestionForm:
            guidance = get_form_prompt_guidance(form, depth=3)
            assert guidance != ""
            assert isinstance(guidance, str)

    def test_guidance_contains_form_description(self):
        """Test that guidance describes the form type."""
        guidance = get_form_prompt_guidance(QuestionForm.CONCEPT, depth=2)
        assert "概念" in guidance or "理解" in guidance

        guidance = get_form_prompt_guidance(QuestionForm.DEBUGGING, depth=3)
        assert "问题" in guidance or "诊断" in guidance

        guidance = get_form_prompt_guidance(QuestionForm.COUNTERFACTUAL, depth=7)
        assert "反事实" in guidance or "改变" in guidance

    def test_guidance_varies_by_form(self):
        """Test that different forms have different guidance."""
        guidance_concept = get_form_prompt_guidance(QuestionForm.CONCEPT, depth=2)
        guidance_debugging = get_form_prompt_guidance(QuestionForm.DEBUGGING, depth=3)
        guidance_cf = get_form_prompt_guidance(QuestionForm.COUNTERFACTUAL, depth=7)

        # All should be different
        assert guidance_concept != guidance_debugging
        assert guidance_concept != guidance_cf
        assert guidance_debugging != guidance_cf
