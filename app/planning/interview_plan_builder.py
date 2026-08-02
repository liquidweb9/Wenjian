"""Interview Plan Builder for Phase 2.

Generates interview plans from claim gap analysis.
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.planning.claim_gap_analyzer import ClaimGapResult, GapType


# ============================================================
# Schemas
# ============================================================

class InterviewTarget(BaseModel):
    """A single target for interview verification."""

    claim_id: str | None = Field(default=None, description="Claim to verify (if gap involves claim)")
    requirement_id: str | None = Field(default=None, description="Requirement to probe (if uncovered)")
    competency_code: str
    priority: float = Field(ge=0.0, le=1.0, description="Priority score 0.0-1.0")
    reason_codes: list[str] = Field(description="Why this target was selected")
    explanation: str = Field(description="Human-readable explanation")
    gap_type: str = Field(description="Type of gap this target addresses")

    # Context for question generation
    claim_text: str | None = None
    requirement_title: str | None = None
    requirement_importance: float | None = None
    requirement_expected_level: int | None = None


class InterviewPlan(BaseModel):
    """Generated interview plan based on claim gap analysis."""

    targets: list[InterviewTarget] = Field(
        description="Interview targets sorted by priority descending"
    )
    total_targets: int
    high_priority_count: int = Field(description="Targets with priority >= 0.7")
    coverage_percentage: float = Field(ge=0.0, le=1.0, description="Job requirement coverage")

    # Summary statistics
    uncovered_count: int = Field(description="Number of uncovered requirements")
    weak_evidence_count: int = Field(description="Number of weak evidence claims")
    supported_count: int = Field(description="Number of supported claims")


# ============================================================
# Interview Plan Builder
# ============================================================

@dataclass
class InterviewPlanBuilder:
    """Builds interview plans from claim gap analysis.

    Strategy:
    1. Include all high-priority gaps (priority >= 0.7)
    2. Include all weak evidence claims (priority >= 0.3, regardless of threshold)
    3. Include 1-2 supported claims for verification
    4. Exclude irrelevant claims
    5. Sort by priority descending
    """

    high_priority_threshold: float = 0.7
    weak_evidence_min_priority: float = 0.3  # Lower threshold for weak evidence
    supported_sample_size: int = 2

    def build_plan(
        self,
        gap_result: ClaimGapResult,
        max_targets: int | None = None,
    ) -> InterviewPlan:
        """Build interview plan from gap analysis.

        Args:
            gap_result: Result from ClaimGapAnalyzer
            max_targets: Optional maximum number of targets (default: no limit)

        Returns:
            Interview plan with prioritized targets
        """
        targets = []

        # Separate gaps by type
        high_priority_gaps = []
        weak_evidence_gaps = []
        supported_gaps = []

        for gap in gap_result.gaps:
            if gap.gap_type == GapType.IRRELEVANT_CLAIM:
                continue  # Skip irrelevant claims

            if gap.priority >= self.high_priority_threshold:
                high_priority_gaps.append(gap)
            elif gap.gap_type in (GapType.WEAK_EVIDENCE_CLAIM, GapType.HIGH_PRIORITY_WEAK_EVIDENCE):
                # Include all weak evidence regardless of priority (they need verification)
                if gap.priority >= self.weak_evidence_min_priority:
                    weak_evidence_gaps.append(gap)
            elif gap.gap_type == GapType.SUPPORTED_CLAIM:
                supported_gaps.append(gap)

        # 1. Add all high-priority gaps
        for gap in high_priority_gaps:
            targets.append(InterviewTarget(
                claim_id=gap.claim_id,
                requirement_id=gap.requirement_id,
                competency_code=gap.competency_code,
                priority=gap.priority,
                reason_codes=[rc.value for rc in gap.reason_codes],
                explanation=gap.explanation,
                gap_type=gap.gap_type.value,
                claim_text=gap.claim_text,
                requirement_title=gap.requirement_title,
                requirement_importance=gap.requirement_importance,
                requirement_expected_level=gap.requirement_expected_level,
            ))

        # 2. Add weak evidence gaps (all of them, they need verification)
        for gap in weak_evidence_gaps:
            targets.append(InterviewTarget(
                claim_id=gap.claim_id,
                requirement_id=gap.requirement_id,
                competency_code=gap.competency_code,
                priority=gap.priority,
                reason_codes=[rc.value for rc in gap.reason_codes],
                explanation=gap.explanation,
                gap_type=gap.gap_type.value,
                claim_text=gap.claim_text,
                requirement_title=gap.requirement_title,
                requirement_importance=gap.requirement_importance,
                requirement_expected_level=gap.requirement_expected_level,
            ))

        # 3. Add sample of supported claims for verification (limited sample)
        for gap in supported_gaps[:self.supported_sample_size]:
            targets.append(InterviewTarget(
                claim_id=gap.claim_id,
                requirement_id=gap.requirement_id,
                competency_code=gap.competency_code,
                priority=gap.priority,
                reason_codes=[rc.value for rc in gap.reason_codes],
                explanation=gap.explanation,
                gap_type=gap.gap_type.value,
                claim_text=gap.claim_text,
                requirement_title=gap.requirement_title,
                requirement_importance=gap.requirement_importance,
                requirement_expected_level=gap.requirement_expected_level,
            ))

        # Already sorted by priority (from gap_result)
        # But re-sort to ensure order after combining lists
        targets.sort(key=lambda t: t.priority, reverse=True)

        # Apply max_targets limit if specified
        if max_targets is not None and len(targets) > max_targets:
            targets = targets[:max_targets]

        # Count gap types
        uncovered_count = sum(
            1 for g in gap_result.gaps
            if g.gap_type == GapType.UNCOVERED_REQUIREMENT
        )
        weak_evidence_count = sum(
            1 for g in gap_result.gaps
            if g.gap_type in (GapType.WEAK_EVIDENCE_CLAIM, GapType.HIGH_PRIORITY_WEAK_EVIDENCE)
        )
        supported_count = sum(
            1 for g in gap_result.gaps
            if g.gap_type == GapType.SUPPORTED_CLAIM
        )

        return InterviewPlan(
            targets=targets,
            total_targets=len(targets),
            high_priority_count=len(high_priority_gaps),
            coverage_percentage=gap_result.coverage_stats.coverage_percentage,
            uncovered_count=uncovered_count,
            weak_evidence_count=weak_evidence_count,
            supported_count=supported_count,
        )

    def explain_target_selection(self, target: InterviewTarget) -> str:
        """Generate detailed explanation for why a target was selected.

        Args:
            target: Interview target

        Returns:
            Human-readable explanation with reason codes
        """
        reason_parts = []

        if "HIGH_IMPORTANCE_GAP" in target.reason_codes:
            reason_parts.append("高优先级需求")

        if "REQUIREMENT_UNCOVERED" in target.reason_codes:
            reason_parts.append("简历未提及")

        if "CLAIM_WEAK_EVIDENCE" in target.reason_codes:
            reason_parts.append("证据不足")

        if "LOW_COVERAGE_LEVEL" in target.reason_codes:
            reason_parts.append(f"覆盖度低于期望（L{target.requirement_expected_level}）")

        if not reason_parts:
            reason_parts.append("需要验证")

        return f"{target.explanation} | 原因：{', '.join(reason_parts)}"
