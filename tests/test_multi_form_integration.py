"""Integration tests for multi-form question generation.

M2.4: Tests end-to-end multi-form question generation with form tracking.
"""

import pytest
from app.interview.question_forms import QuestionForm
from app.interview.counterfactual import CounterfactualGenerator


class TestMultiFormIntegration:
    """Test multi-form question generation integration."""

    def test_form_history_prevents_repetition(self):
        """Test that form history is used to avoid repetition."""
        from app.interview.question_forms import QuestionFormSelector

        selector = QuestionFormSelector()
        competency = "backend.api_design"

        # Generate forms for multiple questions
        forms_used = []
        for depth in [2, 3, 4, 5]:
            form = selector.select_form(
                competency_code=competency,
                current_depth=depth,
                project_context_available=True,
                form_history=forms_used,
            )
            forms_used.append(form.value)

        # Should have different forms
        assert len(set(forms_used)) > 1

    def test_high_importance_competency_gets_multiple_forms(self):
        """Test that high-importance competencies use multiple question forms."""
        from app.interview.question_forms import QuestionFormSelector

        selector = QuestionFormSelector()
        competency = "backend.distributed_systems"

        # Simulate interview progression
        forms_used = []
        depths = [2, 3, 4, 5, 6]

        for depth in depths:
            form = selector.select_form(
                competency_code=competency,
                current_depth=depth,
                project_context_available=True,
                form_history=forms_used,
            )
            forms_used.append(form.value)

        # Should use at least 3 different forms for high-importance
        unique_forms = set(forms_used)
        assert len(unique_forms) >= 3

    def test_counterfactual_generation_with_verified_facts(self):
        """Test counterfactual generation uses verified facts."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "电商推荐系统",
            "tech_stack": ["Redis", "Kafka", "TensorFlow"],
        }

        verified_facts = [
            "系统QPS达到5万",
            "使用Redis缓存热门商品",
            "实时处理用户行为数据",
        ]

        scenarios = generator.generate_constraint_changes(project_context, verified_facts)

        # Should generate scale scenario based on QPS
        scale_scenarios = [s for s in scenarios if s["change_type"] == "scale"]
        assert len(scale_scenarios) > 0

        # Should use verified QPS info
        scale_scenario = scale_scenarios[0]
        assert "QPS" in scale_scenario["description"] or "5" in scale_scenario["description"]

    def test_counterfactual_question_references_project(self):
        """Test that counterfactual questions reference the actual project."""
        generator = CounterfactualGenerator()

        scenario = {
            "change_type": "scale",
            "description": "如果请求量增加100倍",
            "question_template": "你的架构会如何调整？",
        }

        project_name = "实时监控平台"
        question = generator.build_counterfactual_question(scenario, project_name, depth=7)

        # Should mention project name
        assert project_name in question

    def test_form_coverage_tracking(self):
        """Test that form coverage is tracked correctly."""
        from app.interview.question_forms import QuestionFormSelector

        selector = QuestionFormSelector()

        form_history = [
            QuestionForm.CONCEPT.value,
            QuestionForm.PROJECT_DETAIL.value,
            QuestionForm.PROJECT_DETAIL.value,
            QuestionForm.DEBUGGING.value,
            QuestionForm.TRADE_OFF.value,
        ]

        coverage = selector.get_form_coverage(form_history)

        # Check counts
        assert coverage[QuestionForm.PROJECT_DETAIL.value] == 2
        assert coverage[QuestionForm.CONCEPT.value] == 1
        assert coverage[QuestionForm.DEBUGGING.value] == 1
        assert coverage[QuestionForm.COUNTERFACTUAL.value] == 0

    def test_untested_abilities_detection(self):
        """Test detection of untested abilities."""
        from app.interview.question_forms import QuestionFormSelector

        selector = QuestionFormSelector()

        # Only tested theoretical and implementation
        form_history = [
            QuestionForm.CONCEPT.value,
            QuestionForm.PROJECT_DETAIL.value,
        ]

        untested = selector.get_untested_abilities(form_history)

        # Should identify several untested abilities
        assert len(untested) > 2
        assert "transfer_ability" in untested
        assert "problem_solving" in untested

    def test_depth_progression_uses_appropriate_forms(self):
        """Test that depth progression uses depth-appropriate forms."""
        from app.interview.question_forms import QuestionFormSelector, FORM_CHARACTERISTICS

        selector = QuestionFormSelector()

        for depth in range(1, 8):
            form = selector.select_form(
                competency_code="backend.api",
                current_depth=depth,
                project_context_available=True,
                form_history=None,
            )

            # Check that selected form is valid for this depth
            min_depth, max_depth = FORM_CHARACTERISTICS[form]["depth_range"]
            assert min_depth <= depth <= max_depth, (
                f"Form {form} (range {min_depth}-{max_depth}) "
                f"selected for depth {depth}"
            )


class TestDuplicateQuestionPrevention:
    """Test duplicate question detection and prevention."""

    def test_form_diversity_reduces_duplicates(self):
        """Test that using different forms reduces question duplication."""
        from app.interview.question_forms import QuestionFormSelector

        selector = QuestionFormSelector()
        competency = "backend.caching"

        # Generate 5 questions with form tracking
        forms = []
        for i in range(5):
            depth = 2 + i  # Depths 2-6
            form = selector.select_form(
                competency_code=competency,
                current_depth=depth,
                project_context_available=True,
                form_history=forms,
            )
            forms.append(form.value)

        # Should have at least 3 different forms
        assert len(set(forms)) >= 3

    def test_semantic_diversity_across_forms(self):
        """Test that different forms test different aspects."""
        from app.interview.question_forms import FORM_CHARACTERISTICS

        abilities_tested = set()
        for form, chars in FORM_CHARACTERISTICS.items():
            abilities_tested.add(chars["tests_ability"])

        # Should test at least 6 different abilities
        assert len(abilities_tested) >= 6


class TestCounterfactualBinding:
    """Test that counterfactual questions bind to project facts."""

    def test_counterfactual_uses_project_tech_stack(self):
        """Test that counterfactual scenarios reference actual tech."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "搜索引擎",
            "tech_stack": ["Elasticsearch", "Kafka", "Redis"],
        }

        scenarios = generator.generate_constraint_changes(project_context, [])

        # Dependency scenarios should reference actual tech
        dependency_scenarios = [s for s in scenarios if s["change_type"] == "dependency"]

        tech_mentioned = False
        for scenario in dependency_scenarios:
            for tech in project_context["tech_stack"]:
                if tech in scenario["description"]:
                    tech_mentioned = True
                    break

        assert tech_mentioned

    def test_counterfactual_respects_verified_scale(self):
        """Test that scale scenarios use verified scale information."""
        generator = CounterfactualGenerator()

        verified_facts = [
            "系统日均处理10亿条数据",
            "支持1000万DAU",
        ]

        scale_info = generator._extract_scale_info(verified_facts)

        # Should extract data or user scale
        assert scale_info is not None
        assert scale_info["metric"] in ["数据", "用户"]
