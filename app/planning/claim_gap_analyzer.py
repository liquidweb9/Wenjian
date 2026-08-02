"""Claim Gap Analyzer for Phase 2.

Analyzes gaps between resume claims and job requirements.
Classifies gaps into types and calculates priority scores.
"""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from app.planning.claim_mapper import ClaimMappingResult, RequirementMapping


# ============================================================
# Gap Types
# ============================================================

class GapType(str, Enum):
    """Types of gaps between claims and requirements."""

    SUPPORTED_CLAIM = "SUPPORTED_CLAIM"
    """Claim is well-supported by evidence (good coverage)."""

    WEAK_EVIDENCE_CLAIM = "WEAK_EVIDENCE_CLAIM"
    """Claim exists but evidence is insufficient or shallow."""

    HIGH_PRIORITY_WEAK_EVIDENCE = "HIGH_PRIORITY_WEAK_EVIDENCE"
    """High-importance requirement with weak evidence."""

    UNCOVERED_REQUIREMENT = "UNCOVERED_REQUIREMENT"
    """Job requirement not mentioned in resume at all."""

    IRRELEVANT_CLAIM = "IRRELEVANT_CLAIM"
    """Claim doesn't map to any job requirement."""


class ReasonCode(str, Enum):
    """Reason codes for why a gap exists."""

    REQUIREMENT_UNCOVERED = "REQUIREMENT_UNCOVERED"
    """Job requirement has no matching claim."""

    CLAIM_WEAK_EVIDENCE = "CLAIM_WEAK_EVIDENCE"
    """Claim exists but needs deeper verification."""

    HIGH_IMPORTANCE_GAP = "HIGH_IMPORTANCE_GAP"
    """High-importance requirement is missing or weak."""

    LOW_COVERAGE_LEVEL = "LOW_COVERAGE_LEVEL"
    """Claim only covers basic level, but requirement expects higher."""

    CONTRADICTORY_CLAIMS = "CONTRADICTORY_CLAIMS"
    """Multiple claims about same competency contradict each other."""

    IRRELEVANT_TO_JOB = "IRRELEVANT_TO_JOB"
    """Claim doesn't relate to job target."""


# ============================================================
# Schemas
# ============================================================

class Gap(BaseModel):
    """A single gap between claims and requirements."""

    gap_type: GapType
    claim_id: str | None = Field(default=None, description="Claim ID (if gap involves a claim)")
    requirement_id: str | None = Field(default=None, description="Requirement ID (if gap involves a requirement)")
    competency_code: str
    priority: float = Field(ge=0.0, le=1.0, description="Priority score 0.0-1.0")
    reason_codes: list[ReasonCode] = Field(description="List of reason codes explaining the gap")
    explanation: str = Field(description="Human-readable explanation")

    # Additional context
    claim_text: str | None = None
    requirement_title: str | None = None
    requirement_importance: float | None = None
    requirement_expected_level: int | None = None
    claim_coverage_level: int | None = None


class CoverageStats(BaseModel):
    """Summary statistics of requirement coverage."""

    total_requirements: int
    covered_requirements: int = Field(description="Requirements with at least some claim coverage")
    uncovered_requirements: int = Field(description="Requirements with no claim coverage")
    weak_evidence_count: int = Field(description="Requirements with weak evidence")
    high_priority_gaps: int = Field(description="High-priority gaps (priority >= 0.7)")

    coverage_percentage: float = Field(ge=0.0, le=1.0, description="Percentage of requirements covered")


class ClaimGapResult(BaseModel):
    """Result of claim gap analysis."""

    gaps: list[Gap] = Field(description="List of identified gaps, sorted by priority descending")
    coverage_stats: CoverageStats
    high_priority_targets: list[str] = Field(
        description="Claim IDs or requirement IDs to prioritize in interview"
    )


# ============================================================
# Claim Gap Analyzer
# ============================================================

@dataclass
class ClaimGapAnalyzer:
    """Analyzes gaps between resume claims and job requirements.

    Classification logic:
    1. UNCOVERED_REQUIREMENT: No claim maps to this requirement
    2. HIGH_PRIORITY_WEAK_EVIDENCE: High importance + (low coverage or low relevance)
    3. WEAK_EVIDENCE_CLAIM: Claim exists but coverage level < expected level
    4. SUPPORTED_CLAIM: Good coverage (coverage_level >= expected_level - 1)
    5. IRRELEVANT_CLAIM: Claim doesn't map to any requirement

    Priority formula:
        priority = (
            job_importance * 0.4 +
            evidence_gap * 0.3 +
            claim_risk * 0.2 +
            verification_value * 0.1
        )
    """

    high_importance_threshold: float = 0.8
    weak_evidence_threshold: float = 0.6

    def analyze_gaps(
        self,
        claim_mappings: list[ClaimMappingResult],
        requirements: list[dict],  # {requirement_id, competency_code, title, importance, expected_level}
    ) -> ClaimGapResult:
        """Analyze gaps between claims and requirements.

        Args:
            claim_mappings: Results from ClaimMapper for all claims
            requirements: Job requirements from JobTarget

        Returns:
            Complete gap analysis with prioritized targets
        """
        gaps = []

        # Build requirement lookup
        req_by_id = {req["requirement_id"]: req for req in requirements}

        # Build claim → requirements mapping
        claim_to_reqs: dict[str, list[RequirementMapping]] = {}
        for claim_result in claim_mappings:
            claim_to_reqs[claim_result.claim_id] = claim_result.requirement_mappings

        # Build requirement → claims mapping
        req_to_claims: dict[str, list[tuple[str, RequirementMapping]]] = {
            req["requirement_id"]: [] for req in requirements
        }
        for claim_result in claim_mappings:
            for req_mapping in claim_result.requirement_mappings:
                req_to_claims[req_mapping.requirement_id].append(
                    (claim_result.claim_id, req_mapping)
                )

        # 1. Analyze each requirement for coverage
        for req in requirements:
            req_id = req["requirement_id"]
            req_importance = req["importance"]
            req_expected_level = req["expected_level"]
            req_title = req.get("title", "")
            comp_code = req["competency_code"]

            claims_for_req = req_to_claims[req_id]

            if not claims_for_req:
                # UNCOVERED_REQUIREMENT
                priority = self._calculate_uncovered_priority(req_importance)
                reason_codes = [ReasonCode.REQUIREMENT_UNCOVERED]
                if req_importance >= self.high_importance_threshold:
                    reason_codes.append(ReasonCode.HIGH_IMPORTANCE_GAP)

                gaps.append(Gap(
                    gap_type=GapType.UNCOVERED_REQUIREMENT,
                    claim_id=None,
                    requirement_id=req_id,
                    competency_code=comp_code,
                    priority=priority,
                    reason_codes=reason_codes,
                    explanation=f"Job requires {req_title} (importance {req_importance:.2f}), but no matching claim found",
                    requirement_title=req_title,
                    requirement_importance=req_importance,
                    requirement_expected_level=req_expected_level,
                ))
            else:
                # Check coverage quality
                best_claim_id, best_mapping = max(
                    claims_for_req,
                    key=lambda x: x[1].relevance
                )

                coverage_level = best_mapping.coverage_level
                relevance = best_mapping.relevance

                # Find claim text
                claim_text = next(
                    (cm.claim_text for cm in claim_mappings if cm.claim_id == best_claim_id),
                    None
                )

                if req_importance >= self.high_importance_threshold and (
                    coverage_level < req_expected_level or relevance < self.weak_evidence_threshold
                ):
                    # HIGH_PRIORITY_WEAK_EVIDENCE
                    priority = self._calculate_weak_evidence_priority(
                        req_importance, coverage_level, req_expected_level, relevance
                    )
                    reason_codes = [
                        ReasonCode.HIGH_IMPORTANCE_GAP,
                        ReasonCode.CLAIM_WEAK_EVIDENCE,
                    ]
                    if coverage_level < req_expected_level:
                        reason_codes.append(ReasonCode.LOW_COVERAGE_LEVEL)

                    gaps.append(Gap(
                        gap_type=GapType.HIGH_PRIORITY_WEAK_EVIDENCE,
                        claim_id=best_claim_id,
                        requirement_id=req_id,
                        competency_code=comp_code,
                        priority=priority,
                        reason_codes=reason_codes,
                        explanation=f"{req_title} is high priority (importance {req_importance:.2f}), but evidence is weak (coverage L{coverage_level}, expected L{req_expected_level})",
                        claim_text=claim_text,
                        requirement_title=req_title,
                        requirement_importance=req_importance,
                        requirement_expected_level=req_expected_level,
                        claim_coverage_level=coverage_level,
                    ))
                elif coverage_level < req_expected_level:
                    # WEAK_EVIDENCE_CLAIM
                    priority = self._calculate_weak_evidence_priority(
                        req_importance, coverage_level, req_expected_level, relevance
                    )
                    gaps.append(Gap(
                        gap_type=GapType.WEAK_EVIDENCE_CLAIM,
                        claim_id=best_claim_id,
                        requirement_id=req_id,
                        competency_code=comp_code,
                        priority=priority,
                        reason_codes=[
                            ReasonCode.CLAIM_WEAK_EVIDENCE,
                            ReasonCode.LOW_COVERAGE_LEVEL,
                        ],
                        explanation=f"Claim mentions {req_title}, but coverage (L{coverage_level}) is below expected (L{req_expected_level})",
                        claim_text=claim_text,
                        requirement_title=req_title,
                        requirement_importance=req_importance,
                        requirement_expected_level=req_expected_level,
                        claim_coverage_level=coverage_level,
                    ))
                else:
                    # SUPPORTED_CLAIM
                    priority = self._calculate_supported_priority(req_importance, relevance)
                    gaps.append(Gap(
                        gap_type=GapType.SUPPORTED_CLAIM,
                        claim_id=best_claim_id,
                        requirement_id=req_id,
                        competency_code=comp_code,
                        priority=priority,
                        reason_codes=[],
                        explanation=f"{req_title} appears well-supported by claim (coverage L{coverage_level}, expected L{req_expected_level})",
                        claim_text=claim_text,
                        requirement_title=req_title,
                        requirement_importance=req_importance,
                        requirement_expected_level=req_expected_level,
                        claim_coverage_level=coverage_level,
                    ))

        # 2. Find irrelevant claims (no requirement mapping)
        for claim_result in claim_mappings:
            if not claim_result.requirement_mappings:
                # IRRELEVANT_CLAIM
                # Use first competency mapping to get a competency_code
                comp_code = (
                    claim_result.competency_mappings[0].competency_code
                    if claim_result.competency_mappings
                    else "unknown"
                )

                gaps.append(Gap(
                    gap_type=GapType.IRRELEVANT_CLAIM,
                    claim_id=claim_result.claim_id,
                    requirement_id=None,
                    competency_code=comp_code,
                    priority=0.1,  # Low priority
                    reason_codes=[ReasonCode.IRRELEVANT_TO_JOB],
                    explanation=f"Claim doesn't relate to any job requirement",
                    claim_text=claim_result.claim_text,
                ))

        # Sort gaps by priority (descending)
        gaps.sort(key=lambda g: g.priority, reverse=True)

        # Calculate coverage stats
        total_reqs = len(requirements)
        uncovered = sum(1 for g in gaps if g.gap_type == GapType.UNCOVERED_REQUIREMENT)
        weak_evidence = sum(
            1 for g in gaps
            if g.gap_type in (GapType.WEAK_EVIDENCE_CLAIM, GapType.HIGH_PRIORITY_WEAK_EVIDENCE)
        )
        covered = total_reqs - uncovered
        high_priority_gaps_count = sum(1 for g in gaps if g.priority >= 0.7)

        coverage_stats = CoverageStats(
            total_requirements=total_reqs,
            covered_requirements=covered,
            uncovered_requirements=uncovered,
            weak_evidence_count=weak_evidence,
            high_priority_gaps=high_priority_gaps_count,
            coverage_percentage=covered / total_reqs if total_reqs > 0 else 0.0,
        )

        # Identify high-priority targets for interview
        high_priority_targets = []
        for gap in gaps:
            if gap.priority >= 0.7:
                if gap.claim_id:
                    high_priority_targets.append(gap.claim_id)
                elif gap.requirement_id:
                    high_priority_targets.append(gap.requirement_id)

        return ClaimGapResult(
            gaps=gaps,
            coverage_stats=coverage_stats,
            high_priority_targets=high_priority_targets,
        )

    def _calculate_uncovered_priority(self, importance: float) -> float:
        """Calculate priority for uncovered requirement.

        Formula: importance * 0.9 (very high base priority)
        """
        return importance * 0.9

    def _calculate_weak_evidence_priority(
        self,
        importance: float,
        coverage_level: int,
        expected_level: int,
        relevance: float,
    ) -> float:
        """Calculate priority for weak evidence.

        Formula:
            priority = (
                importance * 0.4 +
                evidence_gap * 0.3 +
                relevance * 0.2 +
                verification_value * 0.1
            )
        """
        # Evidence gap (0.0-1.0, higher = larger gap)
        evidence_gap = max(0.0, (expected_level - coverage_level) / 5.0)

        # Verification value (high if important + large gap)
        verification_value = importance * evidence_gap

        priority = (
            importance * 0.4 +
            evidence_gap * 0.3 +
            (1.0 - relevance) * 0.2 +  # Lower relevance = higher priority to verify
            verification_value * 0.1
        )

        return min(1.0, priority)

    def _calculate_supported_priority(self, importance: float, relevance: float) -> float:
        """Calculate priority for supported claim.

        Even supported claims may need verification in interview, but lower priority.

        Formula: importance * 0.3 + relevance * 0.1
        """
        return importance * 0.3 + relevance * 0.1
