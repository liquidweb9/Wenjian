"""Tests for Evidence Span Extractor."""

import pytest

from app.evidence.span_extractor import (
    EvidenceSpan,
    EvidenceSpanExtractor,
    ExtractionResult,
    EvidenceSpanOutput,
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


class TestEvidenceSpanExtractor:
    """Test evidence span extraction."""

    @pytest.mark.asyncio
    async def test_extract_single_span(self):
        """Extract a single evidence span."""
        mock_llm = MockLLMGateway({
            "spans": [
                {
                    "start": 0,
                    "end": 35,
                    "text": "I implemented Redis caching for APIs",
                    "type": "DIRECT",
                }
            ],
            "summary": "Direct evidence of Redis implementation",
            "confidence": 0.9,
        })

        extractor = EvidenceSpanExtractor(llm=mock_llm)

        result = await extractor.extract_spans(
            answer_text="I implemented Redis caching for APIs to reduce database load.",
            answer_id="ans_123",
            verification_point={
                "aspect": "Redis caching implementation",
                "expected_evidence": {"types": ["implementation_details"]},
            },
        )

        assert len(result.spans) == 1
        assert result.spans[0].answer_id == "ans_123"
        assert result.spans[0].start == 0
        assert result.spans[0].end == 35
        assert "Redis" in result.spans[0].text
        assert result.spans[0].quote_hash.startswith("sha256:")
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_extract_multiple_spans(self):
        """Extract multiple evidence spans."""
        answer_text = "I set up Redis cluster with replication and implemented cache invalidation logic."

        mock_llm = MockLLMGateway({
            "spans": [
                {
                    "start": 0,
                    "end": 22,
                    "text": "I set up Redis cluster",
                    "type": "DIRECT",
                },
                {
                    "start": 44,
                    "end": 74,
                    "text": "implemented cache invalidation",
                    "type": "DIRECT",
                },
            ],
            "summary": "Multiple evidence points for caching",
            "confidence": 0.85,
        })

        extractor = EvidenceSpanExtractor(llm=mock_llm)

        result = await extractor.extract_spans(
            answer_text=answer_text,
            answer_id="ans_123",
            verification_point={
                "aspect": "Distributed caching",
                "expected_evidence": {},
            },
        )

        assert len(result.spans) == 2
        assert result.spans[0].evidence_type == "DIRECT"
        assert result.spans[1].evidence_type == "DIRECT"

    @pytest.mark.asyncio
    async def test_extract_no_evidence(self):
        """Extract when no evidence found."""
        mock_llm = MockLLMGateway({
            "spans": [],
            "summary": "No relevant evidence found",
            "confidence": 0.2,
        })

        extractor = EvidenceSpanExtractor(llm=mock_llm)

        result = await extractor.extract_spans(
            answer_text="I haven't worked with Redis before.",
            answer_id="ans_123",
            verification_point={
                "aspect": "Redis experience",
                "expected_evidence": {},
            },
        )

        assert len(result.spans) == 0
        assert result.confidence == 0.2

    @pytest.mark.asyncio
    async def test_evidence_types(self):
        """Extract different evidence types."""
        answer_text = "I configured Redis sentinel for high availability. The team relied on my expertise."

        mock_llm = MockLLMGateway({
            "spans": [
                {
                    "start": 0,
                    "end": 27,
                    "text": "I configured Redis sentinel",
                    "type": "DIRECT",
                },
                {
                    "start": 55,
                    "end": 82,
                    "text": "team relied on my expertise",
                    "type": "INDIRECT",
                },
            ],
            "summary": "Direct and indirect evidence",
            "confidence": 0.75,
        })

        extractor = EvidenceSpanExtractor(llm=mock_llm)

        result = await extractor.extract_spans(
            answer_text=answer_text,
            answer_id="ans_123",
            verification_point={"aspect": "Redis expertise", "expected_evidence": {}},
        )

        assert len(result.spans) == 2
        assert result.spans[0].evidence_type == "DIRECT"
        assert result.spans[1].evidence_type == "INDIRECT"

    @pytest.mark.asyncio
    async def test_llm_receives_correct_prompt(self):
        """LLM receives properly formatted prompt."""
        mock_llm = MockLLMGateway({
            "spans": [],
            "summary": "Test summary with enough characters",
            "confidence": 0.5,
        })

        extractor = EvidenceSpanExtractor(llm=mock_llm)

        await extractor.extract_spans(
            answer_text="Test answer",
            answer_id="ans_123",
            verification_point={
                "aspect": "Test aspect",
                "expected_evidence": {"key": "value"},
            },
        )

        assert mock_llm.last_task_name == "evidence_span_extraction"
        assert len(mock_llm.last_messages) == 2
        assert mock_llm.last_messages[0]["role"] == "system"
        assert "expert" in mock_llm.last_messages[0]["content"].lower()
        assert "Test aspect" in mock_llm.last_messages[1]["content"]
        assert "Test answer" in mock_llm.last_messages[1]["content"]


class TestSpanValidation:
    """Test span validation logic."""

    def test_validate_valid_span(self):
        """Valid span passes validation."""
        extractor = EvidenceSpanExtractor(llm=None)

        span_data = {
            "start": 0,
            "end": 10,
            "text": "Hello test",
        }

        is_valid = extractor._validate_span(span_data, "Hello test world")
        assert is_valid is True

    def test_validate_span_position_mismatch(self):
        """Span with wrong position fails."""
        extractor = EvidenceSpanExtractor(llm=None)

        span_data = {
            "start": 0,
            "end": 5,
            "text": "Wrong",  # Actual text at 0:5 is "Hello"
        }

        is_valid = extractor._validate_span(span_data, "Hello test")
        assert is_valid is False

    def test_validate_span_invalid_position(self):
        """Span with invalid position fails."""
        extractor = EvidenceSpanExtractor(llm=None)

        # start >= end
        span_data = {
            "start": 10,
            "end": 5,
            "text": "Test",
        }
        is_valid = extractor._validate_span(span_data, "Hello test")
        assert is_valid is False

        # end > text length
        span_data = {
            "start": 0,
            "end": 100,
            "text": "Test",
        }
        is_valid = extractor._validate_span(span_data, "Hello test")
        assert is_valid is False

    def test_validate_span_too_short(self):
        """Span that is too short fails."""
        extractor = EvidenceSpanExtractor(llm=None)

        span_data = {
            "start": 0,
            "end": 3,
            "text": "Hi",
        }

        is_valid = extractor._validate_span(span_data, "Hi there")
        assert is_valid is False  # Less than 5 chars

    def test_validate_span_whitespace_normalized(self):
        """Span with whitespace differences passes."""
        extractor = EvidenceSpanExtractor(llm=None)

        span_data = {
            "start": 0,
            "end": 11,
            "text": "Hello world",
        }

        is_valid = extractor._validate_span(span_data, "Hello world end")
        assert is_valid is True

    def test_validate_span_missing_fields(self):
        """Span with missing fields fails."""
        extractor = EvidenceSpanExtractor(llm=None)

        # Missing 'end'
        span_data = {"start": 0, "text": "Test"}
        is_valid = extractor._validate_span(span_data, "Test text")
        assert is_valid is False


class TestHashCalculation:
    """Test quote hash calculation."""

    def test_calculate_hash(self):
        """Calculate hash for text."""
        extractor = EvidenceSpanExtractor(llm=None)

        hash1 = extractor._calculate_hash("Hello world")
        assert hash1.startswith("sha256:")
        assert len(hash1) == 23  # "sha256:" + 16 hex chars

        # Same text produces same hash
        hash2 = extractor._calculate_hash("Hello world")
        assert hash1 == hash2

        # Different text produces different hash
        hash3 = extractor._calculate_hash("Hello universe")
        assert hash1 != hash3

    def test_hash_different_for_different_text(self):
        """Different texts produce different hashes."""
        extractor = EvidenceSpanExtractor(llm=None)

        hash1 = extractor._calculate_hash("Redis caching")
        hash2 = extractor._calculate_hash("Redis cluster")

        assert hash1 != hash2


class TestExtractionResult:
    """Test ExtractionResult structure."""

    def test_extraction_result_creation(self):
        """Create extraction result."""
        span = EvidenceSpan(
            answer_id="ans_123",
            start=0,
            end=10,
            text="Test span",
            quote_hash="sha256:abc123",
            evidence_type="DIRECT",
        )

        result = ExtractionResult(
            spans=[span],
            summary="Test summary",
            confidence=0.8,
            extracted_by="MODEL",
        )

        assert len(result.spans) == 1
        assert result.summary == "Test summary"
        assert result.confidence == 0.8
        assert result.extracted_by == "MODEL"

    def test_extraction_result_default_extracted_by(self):
        """ExtractionResult has default extracted_by."""
        result = ExtractionResult(
            spans=[],
            summary="Test",
            confidence=0.5,
        )

        assert result.extracted_by == "MODEL"
