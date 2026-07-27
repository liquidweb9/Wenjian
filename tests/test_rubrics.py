"""Tests for scoring rubrics and weighted calculations."""
import pytest
from app.interview.rubrics import calculate_weighted_score, DIMENSION_WEIGHTS


class TestWeightedScore:
    def test_empty_dimensions(self):
        assert calculate_weighted_score({"dimensions": []}) == 0.0

    def test_empty_evaluation(self):
        assert calculate_weighted_score({}) == 0.0

    def test_known_dimensions(self):
        score = calculate_weighted_score({
            "dimensions": [
                {"score": 100, "dimension": "technical_correctness"},
            ]
        })
        assert score == 100.0

    def test_all_dimensions_full_marks(self):
        dims = [{"score": 100, "dimension": d} for d in DIMENSION_WEIGHTS]
        score = calculate_weighted_score({"dimensions": dims})
        assert score == 100.0

    def test_mixed_scores(self):
        dims = [
            {"score": 80, "dimension": "technical_correctness"},
            {"score": 60, "dimension": "implementation_depth"},
            {"score": 100, "dimension": "architecture_tradeoffs"},
            {"score": 70, "dimension": "personal_contribution"},
            {"score": 50, "dimension": "production_awareness"},
            {"score": 90, "dimension": "clarity"},
        ]
        # Weighted: (80*25 + 60*20 + 100*15 + 70*15 + 50*15 + 90*10) / 100
        expected = (80*25 + 60*20 + 100*15 + 70*15 + 50*15 + 90*10) / 100
        assert calculate_weighted_score({"dimensions": dims}) == expected

    def test_unknown_dimension_ignored(self):
        """Unknown dimensions get weight 0, don't affect total."""
        dims = [
            {"score": 100, "dimension": "technical_correctness"},
            {"score": 0, "dimension": "unknown_metric"},
        ]
        # Only technical_correctness counts: 100*25 / 25 = 100
        assert calculate_weighted_score({"dimensions": dims}) == 100.0

    def test_weight_totals_100(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert total == 100, f"Dimension weights must sum to 100, got {total}"
