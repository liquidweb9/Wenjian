"""Tests for ability aggregator.

M2.5: Tests cross-session stability calculation and aggregation logic.
"""

import pytest
from datetime import datetime, timedelta
from app.abilities.aggregator import (
    AbilityAggregator,
    StabilityLevel,
    TransferStatus,
    ScoreTrend,
)


class TestAbilityAggregator:
    """Test ability observation aggregation."""

    def test_aggregate_single_observation(self):
        """Test aggregation with single observation."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "observation_id": "obs1",
                "question_count": 3,
                "question_forms": ["concept", "project_detail"],
                "avg_score": 75.0,
                "max_depth": 4,
                "verification_points_addressed": 2,
                "verification_points_verified": 1,
                "evidence_strength": 0.7,
                "evidence_status": "PARTIALLY_SUPPORTED",
                "contradiction_count": 0,
                "created_at": datetime.utcnow(),
            }
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["total_interviews"] == 1
        assert profile["total_questions"] == 3
        assert profile["avg_score"] == 75.0
        assert profile["stability"] == StabilityLevel.LOW  # Single session = LOW
        assert "SINGLE_SESSION_ONLY" in profile["unresolved_gaps"]

    def test_aggregate_multiple_observations_high_stability(self):
        """Test aggregation with multiple observations achieving high stability."""
        aggregator = AbilityAggregator()

        base_time = datetime.utcnow()
        observations = [
            {
                "question_count": 4,
                "question_forms": ["concept", "project_detail", "debugging"],
                "avg_score": 78.0,
                "max_depth": 5,
                "verification_points_addressed": 3,
                "verification_points_verified": 2,
                "evidence_strength": 0.85,
                "evidence_status": "VERIFIED",
                "contradiction_count": 0,
                "created_at": base_time,
            },
            {
                "question_count": 3,
                "question_forms": ["design_rationale", "trade_off"],
                "avg_score": 80.0,
                "max_depth": 6,
                "verification_points_addressed": 2,
                "verification_points_verified": 2,
                "evidence_strength": 0.88,
                "evidence_status": "VERIFIED",
                "contradiction_count": 0,
                "created_at": base_time + timedelta(days=7),
            },
            {
                "question_count": 5,
                "question_forms": ["counterfactual", "production_scenario"],
                "avg_score": 82.0,
                "max_depth": 7,
                "verification_points_addressed": 4,
                "verification_points_verified": 3,
                "evidence_strength": 0.90,
                "evidence_status": "VERIFIED",
                "contradiction_count": 0,
                "created_at": base_time + timedelta(days=14),
            },
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["total_interviews"] == 3
        assert profile["total_questions"] == 12
        assert profile["stability"] == StabilityLevel.HIGH
        assert len(profile["forms_used"]) == 7  # All unique forms
        # Transfer status is PARTIAL because only 1 counterfactual observation
        assert profile["transfer_status"] in [TransferStatus.PARTIAL, TransferStatus.DEMONSTRATED]
        assert profile["last_evidence_status"] == "VERIFIED"

    def test_stability_calculation_low(self):
        """Test low stability with single session."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 2,
                "question_forms": ["concept"],
                "avg_score": 60.0,
                "evidence_strength": 0.5,
                "created_at": datetime.utcnow(),
            }
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["stability"] == StabilityLevel.LOW
        assert profile["stability_factors"]["session_count"] == 1
        assert profile["stability_factors"]["form_diversity"] == 1

    def test_stability_calculation_medium(self):
        """Test medium stability with 2 sessions and moderate forms."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 3,
                "question_forms": ["concept", "project_detail"],
                "avg_score": 70.0,
                "evidence_strength": 0.65,
                "created_at": datetime.utcnow(),
            },
            {
                "question_count": 2,
                "question_forms": ["debugging"],
                "avg_score": 68.0,
                "evidence_strength": 0.70,
                "created_at": datetime.utcnow() + timedelta(days=3),
            },
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["stability"] == StabilityLevel.MEDIUM
        assert profile["stability_factors"]["session_count"] == 2
        assert profile["stability_factors"]["form_diversity"] == 3

    def test_score_trend_improving(self):
        """Test improving score trend detection."""
        aggregator = AbilityAggregator()

        observations = [
            {"avg_score": 60.0, "question_count": 2, "question_forms": ["concept"], "evidence_strength": 0.5, "created_at": datetime.utcnow()},
            {"avg_score": 65.0, "question_count": 3, "question_forms": ["debugging"], "evidence_strength": 0.6, "created_at": datetime.utcnow()},
            {"avg_score": 72.0, "question_count": 2, "question_forms": ["trade_off"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 78.0, "question_count": 3, "question_forms": ["counterfactual"], "evidence_strength": 0.8, "created_at": datetime.utcnow()},
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["score_trend"] == ScoreTrend.IMPROVING

    def test_score_trend_declining(self):
        """Test declining score trend detection."""
        aggregator = AbilityAggregator()

        observations = [
            {"avg_score": 80.0, "question_count": 2, "question_forms": ["concept"], "evidence_strength": 0.8, "created_at": datetime.utcnow()},
            {"avg_score": 75.0, "question_count": 3, "question_forms": ["debugging"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 68.0, "question_count": 2, "question_forms": ["trade_off"], "evidence_strength": 0.6, "created_at": datetime.utcnow()},
            {"avg_score": 62.0, "question_count": 3, "question_forms": ["project_detail"], "evidence_strength": 0.5, "created_at": datetime.utcnow()},
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["score_trend"] == ScoreTrend.DECLINING

    def test_score_trend_stable(self):
        """Test stable score trend detection."""
        aggregator = AbilityAggregator()

        observations = [
            {"avg_score": 72.0, "question_count": 2, "question_forms": ["concept"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 74.0, "question_count": 3, "question_forms": ["debugging"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 71.0, "question_count": 2, "question_forms": ["trade_off"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 73.0, "question_count": 3, "question_forms": ["project_detail"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["score_trend"] == ScoreTrend.STABLE

    def test_transfer_status_untested(self):
        """Test untested transfer status."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 3,
                "question_forms": ["concept", "project_detail"],
                "avg_score": 75.0,
                "evidence_strength": 0.7,
                "created_at": datetime.utcnow(),
            }
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["transfer_status"] == TransferStatus.UNTESTED
        assert profile["counterfactual_performance"] is None

    def test_transfer_status_partial(self):
        """Test partial transfer status."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 3,
                "question_forms": ["counterfactual", "project_detail"],
                "avg_score": 65.0,
                "evidence_strength": 0.6,
                "created_at": datetime.utcnow(),
            }
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["transfer_status"] == TransferStatus.PARTIAL
        assert profile["counterfactual_performance"] is not None

    def test_transfer_status_demonstrated(self):
        """Test demonstrated transfer status."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 4,
                "question_forms": ["counterfactual", "evolution"],
                "avg_score": 80.0,
                "evidence_strength": 0.85,
                "created_at": datetime.utcnow(),
            },
            {
                "question_count": 3,
                "question_forms": ["counterfactual", "trade_off"],
                "avg_score": 78.0,
                "evidence_strength": 0.82,
                "created_at": datetime.utcnow() + timedelta(days=5),
            },
        ]

        profile = aggregator.aggregate_observations(observations)

        assert profile["transfer_status"] == TransferStatus.DEMONSTRATED
        assert profile["counterfactual_performance"] >= 75

    def test_gap_identification_comprehensive(self):
        """Test comprehensive gap identification."""
        aggregator = AbilityAggregator()

        observations = [
            {
                "question_count": 2,
                "question_forms": ["concept"],
                "avg_score": 55.0,
                "max_depth": 3,
                "evidence_strength": 0.4,
                "evidence_status": "PARTIALLY_SUPPORTED",
                "contradiction_count": 1,
                "created_at": datetime.utcnow(),
            }
        ]

        profile = aggregator.aggregate_observations(observations)

        gaps = profile["unresolved_gaps"]
        assert "SINGLE_SESSION_ONLY" in gaps
        assert "LIMITED_FORM_DIVERSITY" in gaps
        assert "NO_TRANSFER_TESTING" in gaps
        assert "INCOMPLETE_EVIDENCE" in gaps
        assert "INSUFFICIENT_DEPTH" in gaps
        assert "UNRESOLVED_CONTRADICTIONS" in gaps

    def test_weighted_average_calculation(self):
        """Test weighted average score calculation."""
        aggregator = AbilityAggregator()

        observations = [
            {"avg_score": 80.0, "question_count": 4, "question_forms": ["concept"], "evidence_strength": 0.8, "created_at": datetime.utcnow()},
            {"avg_score": 70.0, "question_count": 2, "question_forms": ["debugging"], "evidence_strength": 0.7, "created_at": datetime.utcnow()},
            {"avg_score": 90.0, "question_count": 3, "question_forms": ["trade_off"], "evidence_strength": 0.9, "created_at": datetime.utcnow()},
        ]

        profile = aggregator.aggregate_observations(observations)

        # Weighted average: (80*4 + 70*2 + 90*3) / (4+2+3) = 810/9 = 90
        expected_avg = (80*4 + 70*2 + 90*3) / 9
        assert abs(profile["avg_score"] - expected_avg) < 0.1

    def test_empty_observations(self):
        """Test handling empty observations list."""
        aggregator = AbilityAggregator()

        profile = aggregator.aggregate_observations([])

        assert profile["total_interviews"] == 0
        assert profile["stability"] == StabilityLevel.LOW
        assert profile["transfer_status"] == TransferStatus.UNTESTED


class TestStabilityFactors:
    """Test individual stability factor calculations."""

    def test_session_factor_progression(self):
        """Test session count factor progression."""
        aggregator = AbilityAggregator()

        # 1 session = 0.0
        obs1 = [{"question_count": 2, "avg_score": 70.0, "question_forms": ["concept"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile1 = aggregator.aggregate_observations(obs1)
        assert profile1["stability_factors"]["session_count"] == 1

        # 2 sessions = 0.5
        obs2 = obs1 + [{"question_count": 2, "avg_score": 72.0, "question_forms": ["debugging"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile2 = aggregator.aggregate_observations(obs2)
        assert profile2["stability_factors"]["session_count"] == 2

        # 3+ sessions = 1.0
        obs3 = obs2 + [{"question_count": 2, "avg_score": 74.0, "question_forms": ["trade_off"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile3 = aggregator.aggregate_observations(obs3)
        assert profile3["stability_factors"]["session_count"] == 3

    def test_form_diversity_factor(self):
        """Test form diversity factor."""
        aggregator = AbilityAggregator()

        # 1 form
        obs1 = [{"question_count": 2, "avg_score": 70.0, "question_forms": ["concept"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile1 = aggregator.aggregate_observations(obs1)
        assert profile1["stability_factors"]["form_diversity"] == 1

        # 2 forms
        obs2 = [{"question_count": 2, "avg_score": 70.0, "question_forms": ["concept", "debugging"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile2 = aggregator.aggregate_observations(obs2)
        assert profile2["stability_factors"]["form_diversity"] == 2

        # 4+ forms
        obs4 = [{"question_count": 2, "avg_score": 70.0, "question_forms": ["concept", "debugging", "trade_off", "counterfactual"], "evidence_strength": 0.7, "created_at": datetime.utcnow()}]
        profile4 = aggregator.aggregate_observations(obs4)
        assert profile4["stability_factors"]["form_diversity"] == 4
