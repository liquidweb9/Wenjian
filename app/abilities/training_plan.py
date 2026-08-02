"""Training plan generator from evidence gaps.

M2.5: Generates actionable training tasks based on interview evidence gaps.
"""

from typing import Any


class TaskType:
    """Training task types."""
    EVIDENCE_COMPLETION = "EVIDENCE_COMPLETION"
    CONCEPT_REVIEW = "CONCEPT_REVIEW"
    DEPTH_IMPROVEMENT = "DEPTH_IMPROVEMENT"
    CONTRADICTION_RESOLUTION = "CONTRADICTION_RESOLUTION"
    FORM_DIVERSIFICATION = "FORM_DIVERSIFICATION"
    TRANSFER_PRACTICE = "TRANSFER_PRACTICE"


class TrainingPlanGenerator:
    """Generate training plans from evidence gaps."""

    def generate_tasks(
        self,
        ability_profile: dict[str, Any],
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
        claim_mappings: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate training tasks from ability profile gaps.

        Args:
            ability_profile: AbilityProfile aggregated data
            competency_code: Competency being assessed
            competency_title: Human-readable competency title
            interview_id: Source interview ID
            resume_id: Resume ID
            user_id: User ID
            claim_mappings: Optional claim-competency mappings for context

        Returns:
            List of training task dicts
        """
        tasks = []
        unresolved_gaps = ability_profile.get("unresolved_gaps", [])
        stability = ability_profile.get("stability", "LOW")
        avg_score = ability_profile.get("avg_score", 0.0)
        forms_used = ability_profile.get("forms_used", [])
        last_evidence_status = ability_profile.get("last_evidence_status", "UNVERIFIED")

        # Task 1: Evidence Completion
        if "INCOMPLETE_EVIDENCE" in unresolved_gaps or last_evidence_status != "VERIFIED":
            tasks.append(self._create_evidence_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
                evidence_status=last_evidence_status,
                claim_mappings=claim_mappings,
            ))

        # Task 2: Form Diversification
        if "LIMITED_FORM_DIVERSITY" in unresolved_gaps:
            tasks.append(self._create_form_diversity_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
                forms_used=forms_used,
            ))

        # Task 3: Transfer Practice
        if "NO_TRANSFER_TESTING" in unresolved_gaps:
            tasks.append(self._create_transfer_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
            ))

        # Task 4: Depth Improvement
        if "INSUFFICIENT_DEPTH" in unresolved_gaps or avg_score < 70:
            tasks.append(self._create_depth_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
                current_avg=avg_score,
            ))

        # Task 5: Contradiction Resolution
        if "UNRESOLVED_CONTRADICTIONS" in unresolved_gaps:
            tasks.append(self._create_contradiction_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
            ))

        # Task 6: Concept Review (if low scores)
        if avg_score < 60:
            tasks.append(self._create_concept_review_task(
                competency_code=competency_code,
                competency_title=competency_title,
                interview_id=interview_id,
                resume_id=resume_id,
                user_id=user_id,
                avg_score=avg_score,
            ))

        # Sort by priority (highest first)
        tasks.sort(key=lambda t: t["priority"], reverse=True)

        return tasks

    def _create_evidence_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
        evidence_status: str,
        claim_mappings: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Create evidence completion task."""
        # Build description with specific claims if available
        if claim_mappings:
            claim_texts = [m.get("claim_text", "") for m in claim_mappings[:3]]
            claim_context = f"涉及简历声明：{'; '.join(claim_texts)}"
        else:
            claim_context = ""

        return {
            "task_type": TaskType.EVIDENCE_COMPLETION,
            "title": f"补充「{competency_title}」的证据",
            "description": (
                f"你的「{competency_title}」能力目前证据状态为 {evidence_status}，"
                f"需要提供更具体的项目细节、技术实现和结果数据来充分证明这一能力。\n\n"
                f"{claim_context}"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_evidence_status": "VERIFIED",
                "required_details": ["项目背景", "技术实现", "具体数据", "个人贡献"],
                "min_verification_points": 2,
            },
            "priority": 0.9,
            "estimated_effort": "MEDIUM",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }

    def _create_form_diversity_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
        forms_used: list[str],
    ) -> dict[str, Any]:
        """Create form diversification task."""
        # Identify untested forms
        all_forms = ["concept", "project_detail", "debugging", "design_rationale", "trade_off", "production_scenario"]
        untested = [f for f in all_forms if f not in forms_used]

        return {
            "task_type": TaskType.FORM_DIVERSIFICATION,
            "title": f"从不同角度验证「{competency_title}」",
            "description": (
                f"你的「{competency_title}」目前仅通过 {len(forms_used)} 种问题形式进行了验证。"
                f"建议从以下角度补充：{', '.join(untested[:3])}，"
                f"以全面展示你的能力深度和广度。"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_form_count": 4,
                "untested_forms": untested[:3],
            },
            "priority": 0.7,
            "estimated_effort": "MEDIUM",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }

    def _create_transfer_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Create transfer ability task."""
        return {
            "task_type": TaskType.TRANSFER_PRACTICE,
            "title": f"练习「{competency_title}」的迁移应用",
            "description": (
                f"你尚未在变化的约束条件下展示「{competency_title}」的迁移能力。"
                f"建议练习反事实场景：如果系统规模增加10倍、如果核心依赖不可用、"
                f"如果需要降低50%成本，你会如何调整方案？"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_transfer_status": "DEMONSTRATED",
                "min_counterfactual_scenarios": 2,
                "min_counterfactual_score": 70,
            },
            "priority": 0.75,
            "estimated_effort": "HIGH",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }

    def _create_depth_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
        current_avg: float,
    ) -> dict[str, Any]:
        """Create depth improvement task."""
        return {
            "task_type": TaskType.DEPTH_IMPROVEMENT,
            "title": f"深化「{competency_title}」的技术深度",
            "description": (
                f"你的「{competency_title}」当前平均分为 {current_avg:.1f}，"
                f"建议从以下方面深化：\n"
                f"• 详细说明设计决策的理由和权衡考量\n"
                f"• 分析生产环境中的边界情况和故障处理\n"
                f"• 对比多种技术方案的优劣势\n"
                f"• 说明系统演进和扩展性考虑"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_avg_score": 75,
                "target_max_depth": 6,
            },
            "priority": 0.8,
            "estimated_effort": "HIGH",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }

    def _create_contradiction_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Create contradiction resolution task."""
        return {
            "task_type": TaskType.CONTRADICTION_RESOLUTION,
            "title": f"澄清「{competency_title}」的矛盾信息",
            "description": (
                f"你在「{competency_title}」的回答中存在矛盾或不一致的信息，"
                f"需要澄清事实或统一表述。建议重新梳理项目时间线、技术选型理由和个人职责边界。"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_contradiction_count": 0,
                "clarification_required": True,
            },
            "priority": 0.95,
            "estimated_effort": "LOW",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }

    def _create_concept_review_task(
        self,
        competency_code: str,
        competency_title: str,
        interview_id: str,
        resume_id: str,
        user_id: str,
        avg_score: float,
    ) -> dict[str, Any]:
        """Create concept review task."""
        return {
            "task_type": TaskType.CONCEPT_REVIEW,
            "title": f"复习「{competency_title}」的核心概念",
            "description": (
                f"你的「{competency_title}」平均分为 {avg_score:.1f}，"
                f"建议复习该领域的核心概念、设计模式和最佳实践，"
                f"确保理论基础扎实后再深入项目细节。"
            ),
            "competency_code": competency_code,
            "completion_criteria": {
                "target_concept_score": 75,
                "recommended_resources": ["官方文档", "设计模式", "最佳实践"],
            },
            "priority": 0.85,
            "estimated_effort": "MEDIUM",
            "interview_id": interview_id,
            "resume_id": resume_id,
            "user_id": user_id,
        }
