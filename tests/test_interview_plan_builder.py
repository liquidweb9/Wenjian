"""Tests for Interview Plan Builder."""

import pytest

from app.planning.claim_mapper import ClaimMapper
from app.planning.claim_gap_analyzer import ClaimGapAnalyzer, GapType
from app.planning.interview_plan_builder import (
    InterviewPlanBuilder,
    InterviewTarget,
    InterviewPlan,
)


class TestInterviewPlanBuilder:
    """Test interview plan building."""

    def test_build_plan_includes_high_priority_gaps(self):
        """High-priority gaps are included in plan."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        # High-importance uncovered requirement
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.95,
                "expected_level": 4,
            }
        ]

        gap_result = analyzer.analyze_gaps([], requirements)
        plan = builder.build_plan(gap_result)

        # Should include the uncovered requirement
        assert plan.total_targets > 0
        assert plan.high_priority_count > 0
        assert any(t.requirement_id == "req_1" for t in plan.targets)

    def test_build_plan_includes_weak_evidence(self):
        """Weak evidence claims are included in plan."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        claim_text = "使用过 Redis"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.75,
                    "expected_level": 3,
                }
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.75,
                "expected_level": 3,
            }
        ]

        gap_result = analyzer.analyze_gaps([claim_result], requirements)
        plan = builder.build_plan(gap_result)

        # Should include weak evidence claim
        assert plan.weak_evidence_count > 0
        assert any(t.claim_id == "claim_1" for t in plan.targets)

    def test_build_plan_samples_supported_claims(self):
        """Supported claims are sampled (limited)."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder(supported_sample_size=2)

        # Create 3 supported claims
        claims = []
        requirements = []

        for i in range(3):
            claim_text = f"深度使用 Redis 缓存技术{i}，包括缓存模式、一致性、分布式锁"
            claim_result = mapper.map_claim(
                claim_id=f"claim_{i}",
                claim_text=claim_text,
                requirements=[
                    {
                        "requirement_id": f"req_{i}",
                        "competency_code": "backend.cache",
                        "title": f"Redis {i}",
                        "importance": 0.7,
                        "expected_level": 2,
                    }
                ],
            )
            claims.append(claim_result)
            requirements.append({
                "requirement_id": f"req_{i}",
                "competency_code": "backend.cache",
                "title": f"Redis {i}",
                "importance": 0.7,
                "expected_level": 2,
            })

        gap_result = analyzer.analyze_gaps(claims, requirements)
        plan = builder.build_plan(gap_result)

        # Should sample only 2 supported claims
        supported_targets = [t for t in plan.targets if t.gap_type == GapType.SUPPORTED_CLAIM.value]
        assert len(supported_targets) <= 2

    def test_build_plan_excludes_irrelevant_claims(self):
        """Irrelevant claims are excluded from plan."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        # Irrelevant claim (frontend)
        claim_text = "负责前端 React 开发"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.8,
                    "expected_level": 3,
                }
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.8,
                "expected_level": 3,
            }
        ]

        gap_result = analyzer.analyze_gaps([claim_result], requirements)
        plan = builder.build_plan(gap_result)

        # Should not include irrelevant claim
        irrelevant_targets = [t for t in plan.targets if t.gap_type == GapType.IRRELEVANT_CLAIM.value]
        assert len(irrelevant_targets) == 0

    def test_build_plan_sorted_by_priority(self):
        """Plan targets are sorted by priority descending."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        # Mix of gaps with different priorities
        claim1 = mapper.map_claim(
            claim_id="claim_1",
            claim_text="使用 Redis",
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.7,
                    "expected_level": 3,
                },
                {
                    "requirement_id": "req_2",
                    "competency_code": "backend.message_queue",
                    "title": "Kafka",
                    "importance": 0.95,
                    "expected_level": 4,
                },
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.7,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_2",
                "competency_code": "backend.message_queue",
                "title": "Kafka",
                "importance": 0.95,
                "expected_level": 4,
            },
        ]

        gap_result = analyzer.analyze_gaps([claim1], requirements)
        plan = builder.build_plan(gap_result)

        # Check sorted by priority
        priorities = [t.priority for t in plan.targets]
        assert priorities == sorted(priorities, reverse=True)

        # Highest priority should be uncovered high-importance requirement
        assert plan.targets[0].requirement_id == "req_2"

    def test_build_plan_respects_max_targets(self):
        """Plan respects max_targets limit."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        # Create multiple gaps
        claims = []
        requirements = []

        for i in range(5):
            claim_text = f"使用 Redis {i}"
            claim_result = mapper.map_claim(
                claim_id=f"claim_{i}",
                claim_text=claim_text,
                requirements=[
                    {
                        "requirement_id": f"req_{i}",
                        "competency_code": "backend.cache",
                        "title": f"Redis {i}",
                        "importance": 0.7,
                        "expected_level": 3,
                    }
                ],
            )
            claims.append(claim_result)
            requirements.append({
                "requirement_id": f"req_{i}",
                "competency_code": "backend.cache",
                "title": f"Redis {i}",
                "importance": 0.7,
                "expected_level": 3,
            })

        gap_result = analyzer.analyze_gaps(claims, requirements)
        plan = builder.build_plan(gap_result, max_targets=3)

        # Should limit to 3 targets
        assert plan.total_targets == 3

    def test_build_plan_statistics(self):
        """Plan includes correct statistics."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        claim1 = mapper.map_claim(
            claim_id="claim_1",
            claim_text="使用 Redis",
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.7,
                    "expected_level": 3,
                },
                {
                    "requirement_id": "req_2",
                    "competency_code": "backend.message_queue",
                    "title": "Kafka",
                    "importance": 0.9,
                    "expected_level": 3,
                },
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.7,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_2",
                "competency_code": "backend.message_queue",
                "title": "Kafka",
                "importance": 0.9,
                "expected_level": 3,
            },
        ]

        gap_result = analyzer.analyze_gaps([claim1], requirements)
        plan = builder.build_plan(gap_result)

        # Check statistics
        assert plan.uncovered_count == 1  # Kafka uncovered
        assert plan.weak_evidence_count == 1  # Redis weak
        assert plan.coverage_percentage == pytest.approx(0.5)  # 1/2 covered


class TestTargetExplanation:
    """Test target explanation generation."""

    def test_explain_high_importance_gap(self):
        """Explanation includes high importance."""
        builder = InterviewPlanBuilder()

        target = InterviewTarget(
            claim_id=None,
            requirement_id="req_1",
            competency_code="backend.cache",
            priority=0.85,
            reason_codes=["REQUIREMENT_UNCOVERED", "HIGH_IMPORTANCE_GAP"],
            explanation="Job requires Redis (importance 0.90), but no matching claim found",
            gap_type="UNCOVERED_REQUIREMENT",
            requirement_title="Redis",
            requirement_importance=0.9,
            requirement_expected_level=3,
        )

        explanation = builder.explain_target_selection(target)

        assert "高优先级需求" in explanation
        assert "简历未提及" in explanation

    def test_explain_weak_evidence(self):
        """Explanation includes weak evidence reason."""
        builder = InterviewPlanBuilder()

        target = InterviewTarget(
            claim_id="claim_1",
            requirement_id="req_1",
            competency_code="backend.cache",
            priority=0.65,
            reason_codes=["CLAIM_WEAK_EVIDENCE", "LOW_COVERAGE_LEVEL"],
            explanation="Redis coverage L1, expected L3",
            gap_type="WEAK_EVIDENCE_CLAIM",
            requirement_title="Redis",
            requirement_importance=0.75,
            requirement_expected_level=3,
        )

        explanation = builder.explain_target_selection(target)

        assert "证据不足" in explanation
        assert "覆盖度低于期望" in explanation
        assert "L3" in explanation


class TestPlanWorkflow:
    """Test complete plan building workflow."""

    def test_complete_workflow(self):
        """Test end-to-end plan building."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()
        builder = InterviewPlanBuilder()

        # Resume claims
        claims = [
            mapper.map_claim(
                claim_id="claim_1",
                claim_text="负责 Redis 缓存架构设计",
                requirements=[
                    {
                        "requirement_id": "req_1",
                        "competency_code": "backend.cache",
                        "title": "Redis 缓存",
                        "importance": 0.9,
                        "expected_level": 4,
                    },
                    {
                        "requirement_id": "req_2",
                        "competency_code": "backend.database_modeling",
                        "title": "MySQL 优化",
                        "importance": 0.85,
                        "expected_level": 3,
                    },
                ],
            ),
        ]

        # Job requirements
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis 缓存",
                "importance": 0.9,
                "expected_level": 4,
            },
            {
                "requirement_id": "req_2",
                "competency_code": "backend.database_modeling",
                "title": "MySQL 优化",
                "importance": 0.85,
                "expected_level": 3,
            },
        ]

        # Analyze gaps
        gap_result = analyzer.analyze_gaps(claims, requirements)

        # Build plan
        plan = builder.build_plan(gap_result)

        # Verify plan structure
        assert plan.total_targets > 0
        assert len(plan.targets) == plan.total_targets
        assert plan.coverage_percentage > 0.0

        # Verify targets have required fields
        for target in plan.targets:
            assert target.competency_code
            assert target.priority >= 0.0
            assert target.explanation
            assert len(target.reason_codes) > 0
