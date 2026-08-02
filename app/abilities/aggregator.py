"""Ability aggregator for cross-session stability calculation.

M2.5: Aggregates ability observations across multiple interviews to assess stability.
"""

from typing import Any


class StabilityLevel:
    """Stability assessment levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TransferStatus:
    """Transfer ability status."""
    UNTESTED = "UNTESTED"
    PARTIAL = "PARTIAL"
    DEMONSTRATED = "DEMONSTRATED"


class ScoreTrend:
    """Score trend over time."""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class AbilityAggregator:
    """Aggregate ability observations across interviews."""

    def __init__(self) -> None:
        """Initialize aggregator."""
        pass

    def aggregate_observations(
        self,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate multiple observations into a profile.

        Args:
            observations: List of AbilityObservation dicts, sorted by created_at

        Returns:
            Profile dict with aggregated metrics
        """
        if not observations:
            return self._empty_profile()

        total_interviews = len(observations)
        total_questions = sum(obs["question_count"] for obs in observations)

        # Collect all forms used
        all_forms = []
        for obs in observations:
            all_forms.extend(obs.get("question_forms", []))
        unique_forms = list(set(all_forms))

        # Calculate weighted average score
        total_score_weight = 0.0
        weighted_sum = 0.0
        for obs in observations:
            weight = obs["question_count"]
            weighted_sum += obs["avg_score"] * weight
            total_score_weight += weight
        avg_score = weighted_sum / total_score_weight if total_score_weight > 0 else 0.0

        # Calculate score trend
        score_trend = self._calculate_score_trend(observations)

        # Calculate stability
        stability, stability_factors = self._calculate_stability(
            observations=observations,
            unique_forms=unique_forms,
            total_interviews=total_interviews,
        )

        # Assess transfer ability
        transfer_status, counterfactual_perf = self._assess_transfer(observations)

        # Get last evidence status
        last_obs = observations[-1]
        last_evidence_status = last_obs.get("evidence_status", "UNVERIFIED")
        last_verification_date = last_obs.get("created_at")

        # Identify unresolved gaps
        unresolved_gaps = self._identify_gaps(observations, unique_forms)

        return {
            "total_interviews": total_interviews,
            "total_questions": total_questions,
            "forms_used": unique_forms,
            "avg_score": round(avg_score, 2),
            "score_trend": score_trend,
            "stability": stability,
            "stability_factors": stability_factors,
            "transfer_status": transfer_status,
            "counterfactual_performance": counterfactual_perf,
            "last_evidence_status": last_evidence_status,
            "last_verification_date": last_verification_date,
            "unresolved_gaps": unresolved_gaps,
        }

    def _calculate_stability(
        self,
        observations: list[dict[str, Any]],
        unique_forms: list[str],
        total_interviews: int,
    ) -> tuple[str, dict[str, Any]]:
        """Calculate stability level based on multiple factors.

        Stability requires:
        - Multiple interviews (cross-session)
        - Multiple question forms (multi-form verification)
        - Consistent performance (low variance)

        Args:
            observations: List of observations
            unique_forms: List of unique forms used
            total_interviews: Total number of interviews

        Returns:
            (stability_level, stability_factors)
        """
        # Factor 1: Session count (cross-session requirement)
        if total_interviews < 2:
            session_factor = 0.0
        elif total_interviews == 2:
            session_factor = 0.5
        else:
            session_factor = 1.0

        # Factor 2: Form diversity (multi-form requirement)
        form_count = len(unique_forms)
        if form_count < 2:
            form_factor = 0.0
        elif form_count == 2:
            form_factor = 0.5
        elif form_count == 3:
            form_factor = 0.75
        else:
            form_factor = 1.0

        # Factor 3: Score consistency (low variance)
        scores = [obs["avg_score"] for obs in observations]
        if len(scores) < 2:
            consistency_factor = 0.0
        else:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5

            # Low std_dev = high consistency
            if std_dev < 5.0:
                consistency_factor = 1.0
            elif std_dev < 10.0:
                consistency_factor = 0.75
            elif std_dev < 15.0:
                consistency_factor = 0.5
            else:
                consistency_factor = 0.25

        # Factor 4: Evidence strength (all observations should have strong evidence)
        evidence_strengths = [obs.get("evidence_strength", 0.0) for obs in observations]
        avg_evidence = sum(evidence_strengths) / len(evidence_strengths) if evidence_strengths else 0.0

        if avg_evidence >= 0.8:
            evidence_factor = 1.0
        elif avg_evidence >= 0.6:
            evidence_factor = 0.75
        elif avg_evidence >= 0.4:
            evidence_factor = 0.5
        else:
            evidence_factor = 0.25

        # Combined stability score
        stability_score = (
            0.30 * session_factor +
            0.30 * form_factor +
            0.25 * consistency_factor +
            0.15 * evidence_factor
        )

        # Determine stability level
        if stability_score >= 0.75:
            stability = StabilityLevel.HIGH
        elif stability_score >= 0.45:
            stability = StabilityLevel.MEDIUM
        else:
            stability = StabilityLevel.LOW

        stability_factors = {
            "session_count": total_interviews,
            "form_diversity": form_count,
            "score_consistency": round(consistency_factor, 2),
            "evidence_strength": round(avg_evidence, 2),
            "stability_score": round(stability_score, 2),
        }

        return stability, stability_factors

    def _calculate_score_trend(self, observations: list[dict[str, Any]]) -> str | None:
        """Calculate score trend across interviews.

        Args:
            observations: List of observations (sorted by created_at)

        Returns:
            IMPROVING/STABLE/DECLINING or None if insufficient data
        """
        if len(observations) < 2:
            return None

        scores = [obs["avg_score"] for obs in observations]

        # Simple linear trend: compare first half vs second half
        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)

        diff = second_half_avg - first_half_avg

        if diff > 5.0:
            return ScoreTrend.IMPROVING
        elif diff < -5.0:
            return ScoreTrend.DECLINING
        else:
            return ScoreTrend.STABLE

    def _assess_transfer(
        self,
        observations: list[dict[str, Any]],
    ) -> tuple[str, float | None]:
        """Assess transfer ability based on counterfactual performance.

        Args:
            observations: List of observations

        Returns:
            (transfer_status, counterfactual_performance)
        """
        # Check if any observation includes counterfactual questions
        counterfactual_obs = [
            obs for obs in observations
            if "counterfactual" in obs.get("question_forms", [])
        ]

        if not counterfactual_obs:
            return TransferStatus.UNTESTED, None

        # Calculate average counterfactual performance
        # (In real implementation, we'd extract counterfactual-specific scores)
        cf_scores = [obs["avg_score"] for obs in counterfactual_obs]
        avg_cf_score = sum(cf_scores) / len(cf_scores)

        # Determine transfer status based on performance
        if len(counterfactual_obs) >= 2 and avg_cf_score >= 75:
            return TransferStatus.DEMONSTRATED, round(avg_cf_score, 2)
        elif avg_cf_score >= 60:
            return TransferStatus.PARTIAL, round(avg_cf_score, 2)
        else:
            return TransferStatus.PARTIAL, round(avg_cf_score, 2)

    def _identify_gaps(
        self,
        observations: list[dict[str, Any]],
        unique_forms: list[str],
    ) -> list[str]:
        """Identify unresolved gaps in ability verification.

        Args:
            observations: List of observations
            unique_forms: Forms used across all interviews

        Returns:
            List of gap types
        """
        gaps = []

        # Gap 1: Low form diversity
        if len(unique_forms) < 3:
            gaps.append("LIMITED_FORM_DIVERSITY")

        # Gap 2: No counterfactual testing
        if "counterfactual" not in unique_forms:
            gaps.append("NO_TRANSFER_TESTING")

        # Gap 3: Evidence not fully verified
        last_obs = observations[-1]
        if last_obs.get("evidence_status") != "VERIFIED":
            gaps.append("INCOMPLETE_EVIDENCE")

        # Gap 4: Low depth reached
        max_depths = [obs.get("max_depth", 0) for obs in observations]
        if max(max_depths) < 6:
            gaps.append("INSUFFICIENT_DEPTH")

        # Gap 5: Contradictions present
        if any(obs.get("contradiction_count", 0) > 0 for obs in observations):
            gaps.append("UNRESOLVED_CONTRADICTIONS")

        # Gap 6: Single session only
        if len(observations) == 1:
            gaps.append("SINGLE_SESSION_ONLY")

        return gaps

    def _empty_profile(self) -> dict[str, Any]:
        """Return empty profile structure."""
        return {
            "total_interviews": 0,
            "total_questions": 0,
            "forms_used": [],
            "avg_score": 0.0,
            "score_trend": None,
            "stability": StabilityLevel.LOW,
            "stability_factors": {
                "session_count": 0,
                "form_diversity": 0,
                "score_consistency": 0.0,
                "evidence_strength": 0.0,
                "stability_score": 0.0,
            },
            "transfer_status": TransferStatus.UNTESTED,
            "counterfactual_performance": None,
            "last_evidence_status": "UNVERIFIED",
            "last_verification_date": None,
            "unresolved_gaps": ["SINGLE_SESSION_ONLY", "LIMITED_FORM_DIVERSITY"],
        }
