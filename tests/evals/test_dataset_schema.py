"""Tests for evaluation dataset loading and schema validation."""

import pytest
from pathlib import Path

from app.evals.datasets import (
    load_golden_dataset,
    get_available_versions,
    ScoringCase,
    RoutingCase,
    EvidenceCase,
)


class TestDatasetLoading:
    """Test dataset file loading."""

    def test_load_scoring_dataset(self):
        """Load scoring golden dataset successfully."""
        cases = load_golden_dataset("scoring", version="v1.0")

        assert len(cases) == 5
        assert all(isinstance(case, ScoringCase) for case in cases)

        # Check first case
        case = cases[0]
        assert case.case_id == "scoring_001"
        assert "Redis caching" in case.question
        assert case.expected_scores.technical_correctness == 22
        assert case.expected_scores.implementation_depth == 16
        assert case.version == "v1.0"

    def test_load_routing_dataset(self):
        """Load routing golden dataset successfully."""
        cases = load_golden_dataset("routing", version="v1.0")

        assert len(cases) == 5
        assert all(isinstance(case, RoutingCase) for case in cases)

        # Check first case
        case = cases[0]
        assert case.case_id == "routing_001"
        assert case.expected_action == "FOLLOW_UP"
        assert case.state.turn_count == 3
        assert case.state.max_turns == 15

    def test_load_evidence_dataset(self):
        """Load evidence golden dataset successfully."""
        cases = load_golden_dataset("evidence", version="v1.0")

        assert len(cases) == 5
        assert all(isinstance(case, EvidenceCase) for case in cases)

        # Check first case
        case = cases[0]
        assert case.case_id == "evidence_001"
        assert case.expected_status == "PARTIALLY_VERIFIED"
        assert case.expected_strength == 65
        assert case.previous_status == "UNTOUCHED"

    def test_nonexistent_dataset_raises_error(self):
        """Raise FileNotFoundError for missing dataset."""
        with pytest.raises(FileNotFoundError):
            load_golden_dataset("scoring", version="v99.0")

    def test_get_available_versions(self):
        """Get list of available dataset versions."""
        versions = get_available_versions("scoring")

        assert "v1.0" in versions
        assert all(v.startswith("v") for v in versions)


class TestScoringCaseSchema:
    """Test scoring case schema validation."""

    def test_valid_scoring_case(self):
        """Create valid scoring case."""
        case = ScoringCase(
            case_id="test_001",
            question="Test question?",
            answer="Test answer.",
            expected_scores={
                "technical_correctness": 20,
                "implementation_depth": 15,
                "architecture_tradeoffs": 10,
                "personal_contribution": 12,
                "production_awareness": 10,
                "clarity": 8,
            },
            reasoning="Test reasoning",
            version="v1.0",
        )

        assert case.case_id == "test_001"
        assert case.expected_scores.technical_correctness == 20

    def test_scoring_out_of_range_rejected(self):
        """Reject scores outside valid ranges."""
        with pytest.raises(Exception):  # Pydantic validation error
            ScoringCase(
                case_id="test_001",
                question="Test?",
                answer="Test.",
                expected_scores={
                    "technical_correctness": 30,  # Max is 25
                    "implementation_depth": 15,
                    "architecture_tradeoffs": 10,
                    "personal_contribution": 12,
                    "production_awareness": 10,
                    "clarity": 8,
                },
                reasoning="Test",
                version="v1.0",
            )


class TestRoutingCaseSchema:
    """Test routing case schema validation."""

    def test_valid_routing_case(self):
        """Create valid routing case."""
        case = RoutingCase(
            case_id="test_001",
            state={
                "turn_count": 5,
                "max_turns": 15,
                "current_claim_id": "claim_test",
                "claim_status": "IN_PROGRESS",
                "current_depth": 2,
                "questions_on_claim": 2,
                "contradictions": [],
                "latest_relevance": 80,
                "latest_implementation_depth": 60,
            },
            latest_evaluation={
                "dimensions": [],
                "strengths": ["Good explanation"],
                "key_missing_points": ["Missing details"],
            },
            expected_action="FOLLOW_UP",
            reasoning="Test reasoning",
            version="v1.0",
        )

        assert case.expected_action == "FOLLOW_UP"
        assert case.state.turn_count == 5

    def test_invalid_action_rejected(self):
        """Reject invalid routing action."""
        with pytest.raises(Exception):  # Pydantic validation error
            RoutingCase(
                case_id="test_001",
                state={
                    "turn_count": 5,
                    "max_turns": 15,
                    "current_claim_id": "claim_test",
                    "claim_status": "IN_PROGRESS",
                    "current_depth": 2,
                    "questions_on_claim": 2,
                    "contradictions": [],
                    "latest_relevance": 80,
                    "latest_implementation_depth": 60,
                },
                latest_evaluation={
                    "dimensions": [],
                    "strengths": [],
                    "key_missing_points": [],
                },
                expected_action="INVALID_ACTION",  # Not in enum
                reasoning="Test",
                version="v1.0",
            )


class TestEvidenceCaseSchema:
    """Test evidence case schema validation."""

    def test_valid_evidence_case(self):
        """Create valid evidence case."""
        case = EvidenceCase(
            case_id="test_001",
            claim="Test claim",
            verification_point="Test VP",
            question="Test question?",
            answer="Test answer.",
            previous_status="UNTOUCHED",
            expected_status="PARTIALLY_VERIFIED",
            expected_strength=70,
            reasoning="Test reasoning",
            version="v1.0",
        )

        assert case.expected_status == "PARTIALLY_VERIFIED"
        assert case.expected_strength == 70

    def test_strength_out_of_range_rejected(self):
        """Reject strength values outside 0-100."""
        with pytest.raises(Exception):  # Pydantic validation error
            EvidenceCase(
                case_id="test_001",
                claim="Test",
                verification_point="Test",
                question="Test?",
                answer="Test.",
                previous_status="UNTOUCHED",
                expected_status="VERIFIED",
                expected_strength=150,  # Max is 100
                reasoning="Test",
                version="v1.0",
            )

    def test_invalid_status_rejected(self):
        """Reject invalid evidence status."""
        with pytest.raises(Exception):  # Pydantic validation error
            EvidenceCase(
                case_id="test_001",
                claim="Test",
                verification_point="Test",
                question="Test?",
                answer="Test.",
                previous_status="INVALID_STATUS",  # Not in enum
                expected_status="VERIFIED",
                expected_strength=80,
                reasoning="Test",
                version="v1.0",
            )
