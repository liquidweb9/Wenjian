"""Tests for Contradiction Detector."""

import pytest

from app.evidence.contradiction_detector import (
    Contradiction,
    ContradictionDetector,
    ContradictionOutput,
    DetectionResult,
)


class MockLLMGateway:
    """Mock LLM for testing."""

    def __init__(self, mock_response: dict):
        self.mock_response = mock_response
        self.last_task_name = None
        self.last_messages = None

    async def generate_structured(
        self,
        task_name: str,
        messages: list[dict],
        output_model: type,
        temperature: float = 0.0,
    ):
        self.last_task_name = task_name
        self.last_messages = messages
        return output_model(**self.mock_response)


class MockIDGenerator:
    """Mock ID generator for testing."""

    def __init__(self):
        self.counter = 0

    def __call__(self):
        self.counter += 1
        return f"ct_{self.counter:03d}"


class TestContradictionDetector:
    """Test contradiction detection."""

    @pytest.mark.asyncio
    async def test_detect_factual_contradiction(self):
        """Detect factual contradiction between answers."""
        mock_llm = MockLLMGateway({
            "contradictions": [
                {
                    "type": "FACTUAL",
                    "severity": "HIGH",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "I used Redis"},
                        {"answer_id": "ans_2", "snippet": "We used Memcached"},
                    ],
                    "description": "Technology choice contradicted between answers",
                }
            ],
            "overall_consistency": "Significant contradiction detected",
            "confidence": 0.9,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_123",
                "aspect": "Caching technology",
                "expected_evidence": {},
            },
            answers=[
                {
                    "answer_id": "ans_1",
                    "question_text": "What caching did you use?",
                    "answer_text": "I used Redis for caching.",
                },
                {
                    "answer_id": "ans_2",
                    "question_text": "Tell me about your cache setup.",
                    "answer_text": "We used Memcached for all caching.",
                },
            ],
        )

        assert len(result.contradictions) == 1
        contradiction = result.contradictions[0]
        assert contradiction.contradiction_id == "ct_001"
        assert contradiction.verification_point_id == "vp_123"
        assert contradiction.contradiction_type == "FACTUAL"
        assert contradiction.severity == "HIGH"
        assert len(contradiction.conflicting_answers) == 2
        assert "clarify" in contradiction.clarification_question.lower()
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_detect_timeline_contradiction(self):
        """Detect timeline contradiction."""
        mock_llm = MockLLMGateway({
            "contradictions": [
                {
                    "type": "TIMELINE",
                    "severity": "MEDIUM",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "6-month project"},
                        {"answer_id": "ans_2", "snippet": "3-month sprint"},
                    ],
                    "description": "Project duration conflicted",
                }
            ],
            "overall_consistency": "Minor timeline inconsistency",
            "confidence": 0.75,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_456",
                "aspect": "Project timeline",
                "expected_evidence": {},
            },
            answers=[
                {
                    "answer_id": "ans_1",
                    "question_text": "How long was the project?",
                    "answer_text": "It was a 6-month project.",
                },
                {
                    "answer_id": "ans_2",
                    "question_text": "What was the timeline?",
                    "answer_text": "We did it in a 3-month sprint.",
                },
            ],
        )

        assert len(result.contradictions) == 1
        assert result.contradictions[0].contradiction_type == "TIMELINE"
        assert result.contradictions[0].severity == "MEDIUM"
        assert "timeline" in result.contradictions[0].clarification_question.lower()

    @pytest.mark.asyncio
    async def test_detect_role_contradiction(self):
        """Detect role contradiction."""
        mock_llm = MockLLMGateway({
            "contradictions": [
                {
                    "type": "ROLE",
                    "severity": "MEDIUM",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "I designed the system"},
                        {"answer_id": "ans_2", "snippet": "Team designed, I implemented"},
                    ],
                    "description": "Role in design phase contradicted",
                }
            ],
            "overall_consistency": "Role description inconsistent",
            "confidence": 0.8,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_789",
                "aspect": "System architecture role",
                "expected_evidence": {},
            },
            answers=[
                {
                    "answer_id": "ans_1",
                    "question_text": "What did you do?",
                    "answer_text": "I designed the system architecture.",
                },
                {
                    "answer_id": "ans_2",
                    "question_text": "Who designed it?",
                    "answer_text": "The team designed it, I implemented the code.",
                },
            ],
        )

        assert len(result.contradictions) == 1
        assert result.contradictions[0].contradiction_type == "ROLE"
        assert "role" in result.contradictions[0].clarification_question.lower()

    @pytest.mark.asyncio
    async def test_detect_scope_contradiction(self):
        """Detect scope contradiction."""
        mock_llm = MockLLMGateway({
            "contradictions": [
                {
                    "type": "SCOPE",
                    "severity": "LOW",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "full system rewrite"},
                        {"answer_id": "ans_2", "snippet": "incremental refactor"},
                    ],
                    "description": "Project scope described differently",
                }
            ],
            "overall_consistency": "Minor scope inconsistency, possibly explained by context",
            "confidence": 0.65,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_999",
                "aspect": "Refactoring scope",
                "expected_evidence": {},
            },
            answers=[
                {
                    "answer_id": "ans_1",
                    "question_text": "What was the scope?",
                    "answer_text": "We did a full system rewrite.",
                },
                {
                    "answer_id": "ans_2",
                    "question_text": "How did you approach it?",
                    "answer_text": "It was an incremental refactor over several sprints.",
                },
            ],
        )

        assert len(result.contradictions) == 1
        assert result.contradictions[0].contradiction_type == "SCOPE"
        assert result.contradictions[0].severity == "LOW"
        assert "scope" in result.contradictions[0].clarification_question.lower()

    @pytest.mark.asyncio
    async def test_detect_multiple_contradictions(self):
        """Detect multiple contradictions."""
        mock_llm = MockLLMGateway({
            "contradictions": [
                {
                    "type": "FACTUAL",
                    "severity": "HIGH",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "Redis"},
                        {"answer_id": "ans_2", "snippet": "Memcached"},
                    ],
                    "description": "Technology contradiction",
                },
                {
                    "type": "TIMELINE",
                    "severity": "MEDIUM",
                    "conflicting_answers": [
                        {"answer_id": "ans_1", "snippet": "2 months"},
                        {"answer_id": "ans_3", "snippet": "6 months"},
                    ],
                    "description": "Timeline contradiction",
                },
            ],
            "overall_consistency": "Multiple contradictions detected",
            "confidence": 0.85,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_multi",
                "aspect": "Caching project",
                "expected_evidence": {},
            },
            answers=[
                {"answer_id": "ans_1", "question_text": "Q1", "answer_text": "A1"},
                {"answer_id": "ans_2", "question_text": "Q2", "answer_text": "A2"},
                {"answer_id": "ans_3", "question_text": "Q3", "answer_text": "A3"},
            ],
        )

        assert len(result.contradictions) == 2
        assert result.contradictions[0].contradiction_type == "FACTUAL"
        assert result.contradictions[1].contradiction_type == "TIMELINE"

    @pytest.mark.asyncio
    async def test_detect_no_contradictions(self):
        """No contradictions detected."""
        mock_llm = MockLLMGateway({
            "contradictions": [],
            "overall_consistency": "Answers are consistent with each other",
            "confidence": 0.9,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_consistent",
                "aspect": "Consistent topic",
                "expected_evidence": {},
            },
            answers=[
                {"answer_id": "ans_1", "question_text": "Q1", "answer_text": "A1"},
                {"answer_id": "ans_2", "question_text": "Q2", "answer_text": "A2"},
            ],
        )

        assert len(result.contradictions) == 0
        assert result.confidence == 0.9
        assert "consistent" in result.overall_consistency.lower()

    @pytest.mark.asyncio
    async def test_insufficient_answers(self):
        """Return early when less than 2 answers."""
        detector = ContradictionDetector(llm=None, id_generator=MockIDGenerator())

        result = await detector.detect_contradictions(
            verification_point={"verification_point_id": "vp_single", "aspect": "Test"},
            answers=[{"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"}],
        )

        assert len(result.contradictions) == 0
        assert result.confidence == 0.0
        assert "insufficient" in result.overall_consistency.lower()

    @pytest.mark.asyncio
    async def test_llm_receives_correct_prompt(self):
        """LLM receives properly formatted prompt."""
        mock_llm = MockLLMGateway({
            "contradictions": [],
            "overall_consistency": "Test consistency with enough characters",
            "confidence": 0.5,
        })

        detector = ContradictionDetector(llm=mock_llm, id_generator=MockIDGenerator())

        await detector.detect_contradictions(
            verification_point={
                "verification_point_id": "vp_test",
                "aspect": "Test aspect",
                "expected_evidence": {"key": "value"},
            },
            answers=[
                {
                    "answer_id": "ans_1",
                    "question_text": "Question 1",
                    "answer_text": "Answer 1",
                },
                {
                    "answer_id": "ans_2",
                    "question_text": "Question 2",
                    "answer_text": "Answer 2",
                },
            ],
        )

        assert mock_llm.last_task_name == "contradiction_detection"
        assert len(mock_llm.last_messages) == 2
        assert mock_llm.last_messages[0]["role"] == "system"
        assert "contradiction" in mock_llm.last_messages[0]["content"].lower()
        assert "Test aspect" in mock_llm.last_messages[1]["content"]
        assert "Answer 1" in mock_llm.last_messages[1]["content"]
        assert "Answer 2" in mock_llm.last_messages[1]["content"]


class TestContradictionValidation:
    """Test contradiction validation logic."""

    def test_validate_valid_contradiction(self):
        """Valid contradiction passes validation."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Redis"},
                {"answer_id": "ans_2", "snippet": "Memcached"},
            ],
            "description": "Technology choice contradicted",
        }

        answers = [
            {"answer_id": "ans_1", "question_text": "Q1", "answer_text": "A1"},
            {"answer_id": "ans_2", "question_text": "Q2", "answer_text": "A2"},
        ]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is True

    def test_validate_missing_fields(self):
        """Contradiction with missing fields fails."""
        detector = ContradictionDetector(llm=None)

        # Missing 'description'
        contradiction_data = {
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Redis"},
            ],
        }

        answers = [{"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"}]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False

    def test_validate_invalid_type(self):
        """Contradiction with invalid type fails."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "INVALID_TYPE",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Test"},
                {"answer_id": "ans_2", "snippet": "Test2"},
            ],
            "description": "Test description",
        }

        answers = [
            {"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"},
            {"answer_id": "ans_2", "question_text": "Q", "answer_text": "A"},
        ]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False

    def test_validate_invalid_severity(self):
        """Contradiction with invalid severity fails."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "FACTUAL",
            "severity": "CRITICAL",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Test"},
                {"answer_id": "ans_2", "snippet": "Test2"},
            ],
            "description": "Test description",
        }

        answers = [
            {"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"},
            {"answer_id": "ans_2", "question_text": "Q", "answer_text": "A"},
        ]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False

    def test_validate_insufficient_conflicts(self):
        """Contradiction with less than 2 conflicting answers fails."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Only one"},
            ],
            "description": "Test description",
        }

        answers = [{"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"}]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False

    def test_validate_nonexistent_answer_id(self):
        """Contradiction referencing nonexistent answer fails."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Test"},
                {"answer_id": "ans_999", "snippet": "Test2"},  # Doesn't exist
            ],
            "description": "Test description",
        }

        answers = [{"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"}]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False

    def test_validate_description_too_short(self):
        """Contradiction with too short description fails."""
        detector = ContradictionDetector(llm=None)

        contradiction_data = {
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {"answer_id": "ans_1", "snippet": "Test"},
                {"answer_id": "ans_2", "snippet": "Test2"},
            ],
            "description": "Short",  # Less than 10 chars
        }

        answers = [
            {"answer_id": "ans_1", "question_text": "Q", "answer_text": "A"},
            {"answer_id": "ans_2", "question_text": "Q", "answer_text": "A"},
        ]

        is_valid = detector._validate_contradiction(contradiction_data, answers)
        assert is_valid is False


class TestClarificationQuestions:
    """Test clarification question generation."""

    def test_factual_clarification(self):
        """Generate clarification for factual contradiction."""
        detector = ContradictionDetector(llm=None)

        question = detector._generate_clarification_question(
            {
                "type": "FACTUAL",
                "description": "Technology choice contradicted between answers",
            },
            {"aspect": "Caching technology"},
        )

        assert "caching technology" in question.lower()
        assert "clarify" in question.lower()
        assert "accurate" in question.lower()

    def test_timeline_clarification(self):
        """Generate clarification for timeline contradiction."""
        detector = ContradictionDetector(llm=None)

        question = detector._generate_clarification_question(
            {"type": "TIMELINE", "description": "Project duration conflicted"},
            {"aspect": "Project timeline"},
        )

        assert "timeline" in question.lower()
        assert "clarify" in question.lower()

    def test_role_clarification(self):
        """Generate clarification for role contradiction."""
        detector = ContradictionDetector(llm=None)

        question = detector._generate_clarification_question(
            {"type": "ROLE", "description": "Role in design phase contradicted"},
            {"aspect": "System design"},
        )

        assert "role" in question.lower()
        assert "clarify" in question.lower()

    def test_scope_clarification(self):
        """Generate clarification for scope contradiction."""
        detector = ContradictionDetector(llm=None)

        question = detector._generate_clarification_question(
            {"type": "SCOPE", "description": "Project scope described differently"},
            {"aspect": "Refactoring scope"},
        )

        assert "scope" in question.lower()
        assert "clarify" in question.lower()


class TestDetectionResult:
    """Test DetectionResult structure."""

    def test_detection_result_creation(self):
        """Create detection result."""
        contradiction = Contradiction(
            contradiction_id="ct_001",
            verification_point_id="vp_123",
            conflicting_answers=[
                {"answer_id": "ans_1", "snippet": "Test1"},
                {"answer_id": "ans_2", "snippet": "Test2"},
            ],
            contradiction_type="FACTUAL",
            severity="HIGH",
            description="Test contradiction",
            clarification_question="Could you clarify?",
        )

        result = DetectionResult(
            contradictions=[contradiction],
            overall_consistency="Test consistency",
            confidence=0.85,
        )

        assert len(result.contradictions) == 1
        assert result.overall_consistency == "Test consistency"
        assert result.confidence == 0.85
        assert result.contradictions[0].contradiction_id == "ct_001"
