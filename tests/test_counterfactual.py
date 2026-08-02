"""Tests for counterfactual question generator.

M2.4: Tests counterfactual scenario generation and question building.
"""

import pytest
from app.interview.counterfactual import CounterfactualGenerator


class TestCounterfactualGenerator:
    """Test counterfactual question generation."""

    def test_generate_constraint_changes_basic(self):
        """Test basic constraint change generation."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "分布式任务调度系统",
            "tech_stack": ["Redis", "RabbitMQ", "PostgreSQL"],
        }

        verified_facts = [
            "系统处理QPS约1000",
            "使用Redis作为缓存",
        ]

        scenarios = generator.generate_constraint_changes(project_context, verified_facts)

        # Should generate multiple scenarios
        assert len(scenarios) > 0

        # Check scenario structure
        for scenario in scenarios:
            assert "change_type" in scenario
            assert "description" in scenario
            assert "original_constraint" in scenario
            assert "new_constraint" in scenario
            assert "question_template" in scenario

    def test_scenario_types_coverage(self):
        """Test that all major scenario types are generated."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "API网关",
            "tech_stack": ["Nginx", "Redis"],
            "timeline": "6个月",
            "team_size": "5人团队",
        }

        verified_facts = []

        scenarios = generator.generate_constraint_changes(project_context, verified_facts)

        # Check that we have diverse scenario types
        scenario_types = {s["change_type"] for s in scenarios}

        expected_types = {"scale", "dependency", "cost", "timeline", "team", "requirement"}
        assert scenario_types == expected_types

    def test_extract_scale_info_from_qps(self):
        """Test scale extraction from QPS mentions."""
        generator = CounterfactualGenerator()

        verified_facts = [
            "系统QPS达到5000",
            "支持高并发请求",
        ]

        scale_info = generator._extract_scale_info(verified_facts)

        assert scale_info is not None
        assert scale_info["metric"] == "QPS"
        assert "current" in scale_info
        assert "increased" in scale_info

    def test_extract_scale_info_from_users(self):
        """Test scale extraction from user count mentions."""
        generator = CounterfactualGenerator()

        verified_facts = [
            "支持100万日活用户",
        ]

        scale_info = generator._extract_scale_info(verified_facts)

        assert scale_info is not None
        assert scale_info["metric"] == "用户"

    def test_extract_scale_info_fallback(self):
        """Test scale extraction fallback when no specific scale mentioned."""
        generator = CounterfactualGenerator()

        verified_facts = [
            "实现了用户认证功能",
        ]

        scale_info = generator._extract_scale_info(verified_facts)

        # Should return default scale scenario
        assert scale_info is not None
        assert "metric" in scale_info
        assert "current" in scale_info

    def test_dependency_scenarios_use_tech_stack(self):
        """Test that dependency scenarios reference actual tech stack."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "实时推荐系统",
            "tech_stack": ["Kafka", "Elasticsearch", "Redis"],
        }

        verified_facts = []

        scenarios = generator.generate_constraint_changes(project_context, verified_facts)

        dependency_scenarios = [s for s in scenarios if s["change_type"] == "dependency"]

        # Should have dependency scenarios for top tech
        assert len(dependency_scenarios) > 0

        # Check that tech stack items are referenced
        tech_mentioned = []
        for scenario in dependency_scenarios:
            desc = scenario["description"]
            for tech in project_context["tech_stack"][:2]:
                if tech in desc:
                    tech_mentioned.append(tech)

        assert len(tech_mentioned) > 0

    def test_build_counterfactual_question_deep(self):
        """Test counterfactual question building for deep depth."""
        generator = CounterfactualGenerator()

        scenario = {
            "change_type": "scale",
            "description": "如果QPS从1000增加到10万",
            "original_constraint": "1000 QPS",
            "new_constraint": "10万 QPS",
            "question_template": "你的方案中哪些部分会成为瓶颈？",
        }

        question = generator.build_counterfactual_question(
            scenario=scenario,
            project_name="分布式缓存系统",
            depth=7,
        )

        # Should include project name
        assert "分布式缓存系统" in question

        # Should include constraint description
        assert "QPS" in question or "10万" in question

        # Should have deep-level framing
        assert "重新设计" in question or "调整架构" in question

    def test_build_counterfactual_question_mid(self):
        """Test counterfactual question building for mid depth."""
        generator = CounterfactualGenerator()

        scenario = {
            "change_type": "dependency",
            "description": "如果Redis不可用",
            "original_constraint": "Redis可用",
            "new_constraint": "Redis故障",
            "question_template": "有什么降级策略？",
        }

        question = generator.build_counterfactual_question(
            scenario=scenario,
            project_name="API服务",
            depth=6,
        )

        # Should be less demanding than deep level
        assert "API服务" in question
        assert "Redis" in question

    def test_build_counterfactual_question_shallow(self):
        """Test counterfactual question building for shallow depth."""
        generator = CounterfactualGenerator()

        scenario = {
            "change_type": "cost",
            "description": "需要降低成本50%",
            "original_constraint": "当前成本",
            "new_constraint": "成本减半",
            "question_template": "你会从哪些方面入手？",
        }

        question = generator.build_counterfactual_question(
            scenario=scenario,
            project_name="数据分析平台",
            depth=5,
        )

        # Should focus on impact rather than complete redesign
        assert "数据分析平台" in question
        assert "成本" in question

    def test_scenario_descriptions_are_chinese(self):
        """Test that all descriptions are in Chinese."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "测试项目",
            "tech_stack": ["Redis"],
        }

        scenarios = generator.generate_constraint_changes(project_context, [])

        for scenario in scenarios:
            # Check that description contains Chinese characters
            description = scenario["description"]
            assert any('一' <= char <= '鿿' for char in description)

            # Check question template
            template = scenario["question_template"]
            assert any('一' <= char <= '鿿' for char in template)

    def test_scenario_coverage_for_empty_tech_stack(self):
        """Test that scenarios are generated even without tech stack."""
        generator = CounterfactualGenerator()

        project_context = {
            "title": "简单服务",
            "tech_stack": [],
        }

        scenarios = generator.generate_constraint_changes(project_context, [])

        # Should still generate non-dependency scenarios
        assert len(scenarios) > 0

        # Should have scale, cost, timeline, team scenarios
        types = {s["change_type"] for s in scenarios}
        assert "scale" in types
        assert "cost" in types
        assert "timeline" in types
