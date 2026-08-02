"""Tests for training plan generator.

M2.5: Tests training task generation from evidence gaps.
"""

import pytest
from app.abilities.training_plan import TrainingPlanGenerator, TaskType


class TestTrainingPlanGenerator:
    """Test training plan generation."""

    def test_generate_tasks_incomplete_evidence(self):
        """Test task generation for incomplete evidence."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INCOMPLETE_EVIDENCE"],
            "stability": "LOW",
            "avg_score": 70.0,
            "forms_used": ["concept", "project_detail"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.caching",
            competency_title="缓存设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have evidence completion task
        evidence_tasks = [t for t in tasks if t["task_type"] == TaskType.EVIDENCE_COMPLETION]
        assert len(evidence_tasks) > 0

        task = evidence_tasks[0]
        assert "补充" in task["title"]
        assert task["competency_code"] == "backend.caching"
        assert task["priority"] > 0.8

    def test_generate_tasks_limited_form_diversity(self):
        """Test task generation for limited form diversity."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["LIMITED_FORM_DIVERSITY"],
            "stability": "LOW",
            "avg_score": 75.0,
            "forms_used": ["concept"],
            "last_evidence_status": "VERIFIED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.api_design",
            competency_title="API设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have form diversity task
        form_tasks = [t for t in tasks if t["task_type"] == TaskType.FORM_DIVERSIFICATION]
        assert len(form_tasks) > 0

        task = form_tasks[0]
        assert "不同角度" in task["title"]
        assert task["completion_criteria"]["target_form_count"] == 4

    def test_generate_tasks_no_transfer_testing(self):
        """Test task generation for missing transfer testing."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["NO_TRANSFER_TESTING"],
            "stability": "MEDIUM",
            "avg_score": 78.0,
            "forms_used": ["concept", "project_detail", "debugging"],
            "last_evidence_status": "VERIFIED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.distributed",
            competency_title="分布式系统",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have transfer practice task
        transfer_tasks = [t for t in tasks if t["task_type"] == TaskType.TRANSFER_PRACTICE]
        assert len(transfer_tasks) > 0

        task = transfer_tasks[0]
        assert "迁移" in task["title"]
        assert task["completion_criteria"]["target_transfer_status"] == "DEMONSTRATED"
        assert task["estimated_effort"] == "HIGH"

    def test_generate_tasks_insufficient_depth(self):
        """Test task generation for insufficient depth."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INSUFFICIENT_DEPTH"],
            "stability": "MEDIUM",
            "avg_score": 65.0,
            "forms_used": ["concept", "project_detail"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.architecture",
            competency_title="架构设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have depth improvement task
        depth_tasks = [t for t in tasks if t["task_type"] == TaskType.DEPTH_IMPROVEMENT]
        assert len(depth_tasks) > 0

        task = depth_tasks[0]
        assert "深化" in task["title"]
        assert task["completion_criteria"]["target_max_depth"] == 6

    def test_generate_tasks_contradictions(self):
        """Test task generation for contradictions."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["UNRESOLVED_CONTRADICTIONS"],
            "stability": "LOW",
            "avg_score": 60.0,
            "forms_used": ["project_detail"],
            "last_evidence_status": "CONTRADICTORY",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.database",
            competency_title="数据库设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have contradiction resolution task
        contradiction_tasks = [t for t in tasks if t["task_type"] == TaskType.CONTRADICTION_RESOLUTION]
        assert len(contradiction_tasks) > 0

        task = contradiction_tasks[0]
        assert "澄清" in task["title"]
        assert task["priority"] > 0.9
        assert task["estimated_effort"] == "LOW"

    def test_generate_tasks_low_score(self):
        """Test task generation for low scores."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INSUFFICIENT_DEPTH"],
            "stability": "LOW",
            "avg_score": 55.0,
            "forms_used": ["concept"],
            "last_evidence_status": "WEAK",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.performance",
            competency_title="性能优化",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have concept review task for very low scores
        concept_tasks = [t for t in tasks if t["task_type"] == TaskType.CONCEPT_REVIEW]
        assert len(concept_tasks) > 0

        task = concept_tasks[0]
        assert "复习" in task["title"]
        assert task["completion_criteria"]["target_concept_score"] == 75

    def test_generate_multiple_tasks_comprehensive(self):
        """Test generation of multiple tasks for comprehensive gaps."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": [
                "INCOMPLETE_EVIDENCE",
                "LIMITED_FORM_DIVERSITY",
                "NO_TRANSFER_TESTING",
                "INSUFFICIENT_DEPTH",
            ],
            "stability": "LOW",
            "avg_score": 60.0,
            "forms_used": ["concept"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.microservices",
            competency_title="微服务架构",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should generate multiple tasks
        assert len(tasks) >= 4

        # Check task types present
        task_types = [t["task_type"] for t in tasks]
        assert TaskType.EVIDENCE_COMPLETION in task_types
        assert TaskType.FORM_DIVERSIFICATION in task_types
        assert TaskType.TRANSFER_PRACTICE in task_types
        assert TaskType.DEPTH_IMPROVEMENT in task_types

    def test_tasks_sorted_by_priority(self):
        """Test that tasks are sorted by priority."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": [
                "INCOMPLETE_EVIDENCE",
                "LIMITED_FORM_DIVERSITY",
                "INSUFFICIENT_DEPTH",
            ],
            "stability": "LOW",
            "avg_score": 65.0,
            "forms_used": ["concept"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.security",
            competency_title="安全设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Check that priorities are descending
        priorities = [t["priority"] for t in tasks]
        assert priorities == sorted(priorities, reverse=True)

    def test_task_with_claim_context(self):
        """Test task generation with claim context."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INCOMPLETE_EVIDENCE"],
            "stability": "LOW",
            "avg_score": 70.0,
            "forms_used": ["concept"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        claim_mappings = [
            {"claim_text": "使用Redis实现分布式锁"},
            {"claim_text": "优化缓存命中率到95%"},
        ]

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.caching",
            competency_title="缓存设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
            claim_mappings=claim_mappings,
        )

        # Evidence task should mention claims
        evidence_tasks = [t for t in tasks if t["task_type"] == TaskType.EVIDENCE_COMPLETION]
        assert len(evidence_tasks) > 0
        assert "Redis" in evidence_tasks[0]["description"]

    def test_no_tasks_for_high_stability(self):
        """Test minimal tasks for high stability profiles."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": [],
            "stability": "HIGH",
            "avg_score": 85.0,
            "forms_used": ["concept", "project_detail", "debugging", "counterfactual"],
            "last_evidence_status": "VERIFIED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.api_design",
            competency_title="API设计",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Should have very few or no tasks
        assert len(tasks) == 0

    def test_completion_criteria_structure(self):
        """Test completion criteria structure."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INCOMPLETE_EVIDENCE"],
            "stability": "LOW",
            "avg_score": 70.0,
            "forms_used": ["concept"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.testing",
            competency_title="测试策略",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        # Check completion criteria structure
        for task in tasks:
            assert "completion_criteria" in task
            assert isinstance(task["completion_criteria"], dict)
            assert len(task["completion_criteria"]) > 0

    def test_task_metadata_complete(self):
        """Test that all task metadata fields are present."""
        generator = TrainingPlanGenerator()

        ability_profile = {
            "unresolved_gaps": ["INSUFFICIENT_DEPTH"],
            "stability": "LOW",
            "avg_score": 65.0,
            "forms_used": ["concept"],
            "last_evidence_status": "PARTIALLY_SUPPORTED",
        }

        tasks = generator.generate_tasks(
            ability_profile=ability_profile,
            competency_code="backend.messaging",
            competency_title="消息队列",
            interview_id="int1",
            resume_id="res1",
            user_id="user1",
        )

        for task in tasks:
            # Required fields
            assert "task_type" in task
            assert "title" in task
            assert "description" in task
            assert "competency_code" in task
            assert "completion_criteria" in task
            assert "priority" in task
            assert "estimated_effort" in task
            assert "interview_id" in task
            assert "resume_id" in task
            assert "user_id" in task

            # Value checks
            assert 0.0 <= task["priority"] <= 1.0
            assert task["estimated_effort"] in ["LOW", "MEDIUM", "HIGH"]
