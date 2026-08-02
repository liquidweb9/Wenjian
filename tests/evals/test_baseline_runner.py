"""Tests for evaluation runner and baseline metrics."""

import pytest

from app.evals.datasets import load_golden_dataset
from app.evals.runner import (
    run_scoring_eval,
    run_routing_eval,
    run_evidence_eval,
    run_baseline_evaluation,
)


class TestScoringEval:
    """Test scoring evaluation runner."""

    def test_scoring_eval_runs(self):
        """Scoring eval completes and returns metrics."""
        cases = load_golden_dataset("scoring", version="v1.0")
        result = run_scoring_eval(cases)

        assert result.total_cases == 5
        assert 0 <= result.overall_mae <= 25  # MAE should be reasonable
        assert 0 <= result.level_agreement_rate <= 1.0

        # Check all dimensions present
        expected_dims = [
            "technical_correctness",
            "implementation_depth",
            "architecture_tradeoffs",
            "personal_contribution",
            "production_awareness",
            "clarity"
        ]
        for dim in expected_dims:
            assert dim in result.mae_per_dimension
            assert dim in result.dimension_miss_rate

    def test_scoring_eval_summary_readable(self):
        """Scoring eval summary is human-readable."""
        cases = load_golden_dataset("scoring", version="v1.0")
        result = run_scoring_eval(cases)

        summary = result.summary()

        assert "Scoring Evaluation Results" in summary
        assert "Overall MAE" in summary
        assert "Level Agreement Rate" in summary
        assert "technical_correctness" in summary


class TestRoutingEval:
    """Test routing evaluation runner."""

    def test_routing_eval_runs(self):
        """Routing eval completes and returns metrics."""
        cases = load_golden_dataset("routing", version="v1.0")
        result = run_routing_eval(cases)

        assert result.total_cases == 5
        assert 0 <= result.accuracy <= 1.0
        assert 0 <= result.invalid_route_rate <= 1.0
        assert 0 <= result.premature_switch_rate <= 1.0
        assert isinstance(result.confusion_matrix, dict)

    def test_routing_eval_summary_readable(self):
        """Routing eval summary is human-readable."""
        cases = load_golden_dataset("routing", version="v1.0")
        result = run_routing_eval(cases)

        summary = result.summary()

        assert "Routing Evaluation Results" in summary
        assert "Accuracy" in summary
        assert "Invalid Route Rate" in summary


class TestEvidenceEval:
    """Test evidence evaluation runner."""

    def test_evidence_eval_runs(self):
        """Evidence eval completes and returns metrics."""
        cases = load_golden_dataset("evidence", version="v1.0")
        result = run_evidence_eval(cases)

        assert result.total_cases == 5
        assert 0 <= result.status_accuracy <= 1.0
        assert 0 <= result.verified_false_positive_rate <= 1.0
        assert 0 <= result.unsupported_false_negative_rate <= 1.0
        assert 0 <= result.contradiction_precision <= 1.0
        assert 0 <= result.contradiction_recall <= 1.0
        assert result.strength_mae >= 0

    def test_evidence_eval_summary_readable(self):
        """Evidence eval summary is human-readable."""
        cases = load_golden_dataset("evidence", version="v1.0")
        result = run_evidence_eval(cases)

        summary = result.summary()

        assert "Evidence Evaluation Results" in summary
        assert "Status Accuracy" in summary
        assert "VERIFIED False Positive Rate" in summary
        assert "Contradiction Precision" in summary


class TestBaselineEvaluation:
    """Test complete baseline evaluation."""

    def test_baseline_evaluation_runs(self):
        """Baseline evaluation runs all three eval types."""
        results = run_baseline_evaluation(dataset_version="v1.0")

        assert "scoring" in results
        assert "routing" in results
        assert "evidence" in results

        # Check each result is correct type
        assert results["scoring"].total_cases == 5
        assert results["routing"].total_cases == 5
        assert results["evidence"].total_cases == 5

    def test_baseline_produces_deterministic_results(self):
        """Running baseline twice produces same results (with mock functions)."""
        results1 = run_baseline_evaluation(dataset_version="v1.0")
        results2 = run_baseline_evaluation(dataset_version="v1.0")

        # With mock evaluators, results should be identical
        assert results1["scoring"].overall_mae == results2["scoring"].overall_mae
        assert results1["routing"].accuracy == results2["routing"].accuracy
        assert results1["evidence"].status_accuracy == results2["evidence"].status_accuracy
