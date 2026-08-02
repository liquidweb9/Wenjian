"""Tests for eval gate regression detection.

M2.3: Tests regression comparison and threshold enforcement.
"""

import pytest
from app.evals.eval_gate import compare_results, REGRESSION_THRESHOLDS


def test_no_regression():
    """Test that identical results show no regression."""
    baseline = {
        "scoring": {
            "overall_mae": 2.5,
            "level_agreement_rate": 0.85,
        },
        "routing": {
            "accuracy": 0.90,
            "invalid_route_rate": 0.02,
        },
        "evidence": {
            "status_accuracy": 0.88,
            "verified_false_positive_rate": 0.05,
        },
    }

    current = baseline.copy()

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is False
    assert len(comparison["regressions"]) == 0


def test_scoring_mae_regression():
    """Test detection of scoring MAE regression."""
    baseline = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.85,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 4.5,  # Increased by 2.5 (> threshold of 2.0)
            "level_agreement_rate": 0.85,
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is True
    assert len(comparison["regressions"]) == 1
    assert comparison["regressions"][0]["metric"] == "overall_mae"
    assert comparison["regressions"][0]["delta"] == 2.5


def test_scoring_agreement_regression():
    """Test detection of level agreement regression."""
    baseline = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.90,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.75,  # Dropped by 0.15 (> threshold of -0.10)
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is True
    assert len(comparison["regressions"]) == 1
    assert comparison["regressions"][0]["metric"] == "level_agreement_rate"
    assert abs(comparison["regressions"][0]["delta"] - (-0.15)) < 0.001


def test_routing_accuracy_regression():
    """Test detection of routing accuracy regression."""
    baseline = {
        "routing": {
            "accuracy": 0.90,
            "invalid_route_rate": 0.02,
        },
    }

    current = {
        "routing": {
            "accuracy": 0.70,  # Dropped by 0.20 (> threshold of -0.15)
            "invalid_route_rate": 0.02,
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is True
    assert len(comparison["regressions"]) == 1
    assert comparison["regressions"][0]["metric"] == "accuracy"


def test_evidence_false_positive_regression():
    """Test detection of VERIFIED false positive regression."""
    baseline = {
        "evidence": {
            "status_accuracy": 0.85,
            "verified_false_positive_rate": 0.05,
        },
    }

    current = {
        "evidence": {
            "status_accuracy": 0.85,
            "verified_false_positive_rate": 0.20,  # Increased by 0.15 (> threshold of 0.10)
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is True
    assert len(comparison["regressions"]) == 1
    assert comparison["regressions"][0]["metric"] == "verified_false_positive_rate"


def test_multiple_regressions():
    """Test detection of multiple regressions across categories."""
    baseline = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.90,
        },
        "routing": {
            "accuracy": 0.90,
            "invalid_route_rate": 0.02,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 5.0,  # Regression
            "level_agreement_rate": 0.75,  # Regression
        },
        "routing": {
            "accuracy": 0.70,  # Regression
            "invalid_route_rate": 0.02,
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is True
    assert len(comparison["regressions"]) == 3


def test_improvements_detected():
    """Test that improvements are detected and reported."""
    baseline = {
        "scoring": {
            "overall_mae": 5.0,
            "level_agreement_rate": 0.70,
        },
        "routing": {
            "accuracy": 0.75,
            "invalid_route_rate": 0.10,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 2.0,  # Improved by 3.0
            "level_agreement_rate": 0.85,  # Improved by 0.15
        },
        "routing": {
            "accuracy": 0.90,  # Improved by 0.15
            "invalid_route_rate": 0.10,
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is False
    assert len(comparison["improvements"]) == 3


def test_within_threshold_no_regression():
    """Test that changes within threshold don't trigger regression."""
    baseline = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.85,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 3.5,  # Increased by 1.5 (< threshold of 2.0)
            "level_agreement_rate": 0.80,  # Dropped by 0.05 (< threshold of -0.10)
        },
    }

    comparison = compare_results(baseline, current)

    assert comparison["has_regression"] is False


def test_edge_case_exactly_at_threshold():
    """Test behavior when delta is exactly at threshold."""
    baseline = {
        "scoring": {
            "overall_mae": 2.0,
            "level_agreement_rate": 0.85,
        },
    }

    current = {
        "scoring": {
            "overall_mae": 4.0,  # Increased by exactly 2.0 (= threshold)
            "level_agreement_rate": 0.75,  # Dropped by exactly -0.10 (= threshold)
        },
    }

    comparison = compare_results(baseline, current)

    # At threshold should NOT trigger regression (must exceed threshold)
    assert comparison["has_regression"] is False
