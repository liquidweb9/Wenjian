"""Evidence Span Extractor for Phase 2.

Extracts specific text spans from interview answers that provide evidence
for claim verification.
"""

import hashlib
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field


# ============================================================
# Data Structures
# ============================================================

class EvidenceSpanOutput(BaseModel):
    """LLM output for evidence span extraction."""

    spans: list[dict] = Field(
        description="Evidence spans extracted from answer",
        min_length=0,
    )
    summary: str = Field(
        description="Brief summary of evidence quality",
        min_length=10,
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in evidence extraction",
    )


@dataclass
class EvidenceSpan:
    """Single evidence span with position and hash."""

    answer_id: str
    start: int
    end: int
    text: str
    quote_hash: str
    evidence_type: str  # DIRECT/INDIRECT/CONTEXTUAL


@dataclass
class ExtractionResult:
    """Result of evidence extraction."""

    spans: list[EvidenceSpan]
    summary: str
    confidence: float
    extracted_by: str = "MODEL"


class LLMGateway(Protocol):
    """Protocol for LLM gateway."""

    async def generate_structured(
        self,
        task_name: str,
        messages: list[dict],
        output_model: type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        """Generate structured output."""
        ...


# ============================================================
# Evidence Span Extractor
# ============================================================

class EvidenceSpanExtractor:
    """Extract evidence spans from interview answers.

    Uses LLM to identify specific text segments that provide evidence
    for claim verification.
    """

    def __init__(self, llm: LLMGateway, model_tier: str | None = None):
        self.llm = llm
        self.model_tier = model_tier

    async def extract_spans(
        self,
        answer_text: str,
        answer_id: str,
        verification_point: dict,
    ) -> ExtractionResult:
        """Extract relevant evidence spans from answer.

        Args:
            answer_text: The interview answer text
            answer_id: Answer identifier
            verification_point: Verification point with aspect and expected_evidence

        Returns:
            ExtractionResult with spans, summary, and confidence
        """
        # Build prompt
        prompt = self._build_extraction_prompt(answer_text, verification_point)

        # Call LLM
        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting evidence from interview answers.",
            },
            {"role": "user", "content": prompt},
        ]

        kwargs: dict = {}
        if self.model_tier is not None:
            kwargs["model_tier"] = self.model_tier

        result = await self.llm.generate_structured(
            task_name="evidence_span_extraction",
            messages=messages,
            output_model=EvidenceSpanOutput,
            temperature=0.0,
            **kwargs,
        )

        # Validate and convert spans
        spans = []
        for span_data in result.spans:
            # Validate span
            if not self._validate_span(span_data, answer_text):
                continue

            # Calculate hash
            quote_hash = self._calculate_hash(span_data["text"])

            # Create span
            span = EvidenceSpan(
                answer_id=answer_id,
                start=span_data["start"],
                end=span_data["end"],
                text=span_data["text"],
                quote_hash=quote_hash,
                evidence_type=span_data.get("type", "DIRECT"),
            )
            spans.append(span)

        return ExtractionResult(
            spans=spans,
            summary=result.summary,
            confidence=result.confidence,
            extracted_by="MODEL",
        )

    def _build_extraction_prompt(
        self,
        answer_text: str,
        verification_point: dict,
    ) -> str:
        """Build prompt for evidence extraction."""
        aspect = verification_point.get("aspect", "")
        expected_evidence = verification_point.get("expected_evidence", {})

        prompt = f"""Extract evidence spans from the interview answer that support or refute the verification aspect.

**Verification Aspect**: {aspect}

**Expected Evidence**: {expected_evidence}

**Interview Answer**:
{answer_text}

**Task**:
1. Identify specific text spans that provide evidence for the verification aspect
2. For each span, provide:
   - start: character position where span starts
   - end: character position where span ends
   - text: the exact quoted text
   - type: DIRECT (explicit statement), INDIRECT (implies), or CONTEXTUAL (background info)
3. Provide a summary of evidence quality
4. Rate your confidence in the extraction (0.0-1.0)

**Rules**:
- Only extract spans that are directly relevant
- Spans must be exact quotes from the answer
- start position must be less than end position
- Multiple spans can overlap if they provide different evidence types
- If no evidence found, return empty spans array

Return JSON with structure:
{{
    "spans": [
        {{"start": 10, "end": 50, "text": "exact quote", "type": "DIRECT"}},
        ...
    ],
    "summary": "Brief summary of evidence quality",
    "confidence": 0.85
}}
"""
        return prompt

    def _validate_span(self, span_data: dict, answer_text: str) -> bool:
        """Validate span data."""
        # Check required fields
        if "start" not in span_data or "end" not in span_data or "text" not in span_data:
            return False

        start = span_data["start"]
        end = span_data["end"]
        text = span_data["text"]

        # Check position validity
        if start < 0 or end > len(answer_text) or start >= end:
            return False

        # Check minimum length
        if len(text.strip()) < 5:
            return False

        # Check text matches - extract actual text from answer
        actual_text = answer_text[start:end]

        # Normalize both texts (whitespace)
        actual_normalized = " ".join(actual_text.split())
        expected_normalized = " ".join(text.split())

        # Allow match if normalized texts are equal
        if actual_normalized == expected_normalized:
            return True

        # Also allow if the expected text is a substring (LLM may extract clean version)
        if expected_normalized in actual_normalized or actual_normalized in expected_normalized:
            return True

        return False

    def _calculate_hash(self, text: str) -> str:
        """Calculate SHA256 hash of text for integrity check."""
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        return f"sha256:{hash_obj.hexdigest()[:16]}"

    def extract_spans_from_multiple_answers(
        self,
        answers: list[dict],
        verification_point: dict,
    ) -> list[ExtractionResult]:
        """Extract spans from multiple answers (for cross-answer analysis).

        This is useful when a verification point spans multiple questions.
        """
        # TODO: Implement batch extraction with cross-reference
        # For now, this is a placeholder for future enhancement
        raise NotImplementedError("Batch extraction not yet implemented")
