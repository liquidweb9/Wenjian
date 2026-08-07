"""Contradiction Detector for Phase 2.

Detects contradictions between interview answers and generates
clarification questions to resolve them.
"""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field


# ============================================================
# Data Structures
# ============================================================

class ContradictionOutput(BaseModel):
    """LLM output for contradiction detection."""

    contradictions: list[dict] = Field(
        description="Detected contradictions between answers",
        min_length=0,
    )
    overall_consistency: str = Field(
        description="Overall consistency assessment",
        min_length=10,
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in contradiction detection",
    )


@dataclass
class Contradiction:
    """Single detected contradiction."""

    contradiction_id: str
    verification_point_id: str
    conflicting_answers: list[dict]  # [{"answer_id": "...", "text": "...", "question": "..."}]
    contradiction_type: str  # FACTUAL/TIMELINE/ROLE/SCOPE
    severity: str  # LOW/MEDIUM/HIGH
    description: str
    clarification_question: str


@dataclass
class DetectionResult:
    """Result of contradiction detection."""

    contradictions: list[Contradiction]
    overall_consistency: str
    confidence: float


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
# Contradiction Detector
# ============================================================

class ContradictionDetector:
    """Detect contradictions between interview answers.

    Analyzes multiple answers related to the same verification point
    to identify factual, timeline, role, or scope contradictions.
    """

    def __init__(self, llm: LLMGateway, id_generator=None, model_tier: str | None = None):
        self.llm = llm
        self.id_generator = id_generator or (lambda: f"ct_{id(self)}")
        self.model_tier = model_tier

    async def detect_contradictions(
        self,
        verification_point: dict,
        answers: list[dict],
    ) -> DetectionResult:
        """Detect contradictions between answers.

        Args:
            verification_point: VP with aspect and expected_evidence
            answers: List of answer dicts with answer_id, question_text, answer_text

        Returns:
            DetectionResult with contradictions, consistency, and confidence
        """
        if len(answers) < 2:
            # Need at least 2 answers to detect contradictions
            return DetectionResult(
                contradictions=[],
                overall_consistency="Insufficient data for contradiction detection",
                confidence=0.0,
            )

        # Build prompt
        prompt = self._build_detection_prompt(verification_point, answers)

        # Call LLM
        messages = [
            {
                "role": "system",
                "content": "You are an expert at detecting contradictions in interview responses.",
            },
            {"role": "user", "content": prompt},
        ]

        kwargs: dict = {}
        if self.model_tier is not None:
            kwargs["model_tier"] = self.model_tier

        result = await self.llm.generate_structured(
            task_name="contradiction_detection",
            messages=messages,
            output_model=ContradictionOutput,
            temperature=0.0,
            **kwargs,
        )

        # Convert to Contradiction objects
        contradictions = []
        for contradiction_data in result.contradictions:
            # Validate contradiction data
            if not self._validate_contradiction(contradiction_data, answers):
                continue

            # Generate clarification question
            clarification = self._generate_clarification_question(
                contradiction_data,
                verification_point,
            )

            # Create contradiction
            contradiction = Contradiction(
                contradiction_id=self.id_generator(),
                verification_point_id=verification_point.get("verification_point_id", ""),
                conflicting_answers=contradiction_data.get("conflicting_answers", []),
                contradiction_type=contradiction_data.get("type", "FACTUAL"),
                severity=contradiction_data.get("severity", "MEDIUM"),
                description=contradiction_data.get("description", ""),
                clarification_question=clarification,
            )
            contradictions.append(contradiction)

        return DetectionResult(
            contradictions=contradictions,
            overall_consistency=result.overall_consistency,
            confidence=result.confidence,
        )

    def _build_detection_prompt(
        self,
        verification_point: dict,
        answers: list[dict],
    ) -> str:
        """Build prompt for contradiction detection."""
        aspect = verification_point.get("aspect", "")
        expected_evidence = verification_point.get("expected_evidence", {})

        # Format answers
        answers_text = ""
        for i, answer in enumerate(answers, 1):
            answers_text += f"\n**Answer {i}** (ID: {answer.get('answer_id', 'unknown')})\n"
            answers_text += f"Question: {answer.get('question_text', '')}\n"
            answers_text += f"Response: {answer.get('answer_text', '')}\n"

        prompt = f"""Analyze interview answers for contradictions related to the verification aspect.

**Verification Aspect**: {aspect}

**Expected Evidence**: {expected_evidence}

**Answers to Analyze**:{answers_text}

**Task**:
1. Identify contradictions between answers regarding:
   - **FACTUAL**: Contradictory facts or claims (e.g., "I used Redis" vs "We used Memcached")
   - **TIMELINE**: Conflicting timelines (e.g., "6 months project" vs "3-month sprint")
   - **ROLE**: Contradictory role descriptions (e.g., "I designed" vs "Team designed, I implemented")
   - **SCOPE**: Contradictory scope claims (e.g., "full system rewrite" vs "incremental refactor")

2. For each contradiction, provide:
   - type: FACTUAL/TIMELINE/ROLE/SCOPE
   - severity: LOW (minor inconsistency), MEDIUM (notable conflict), HIGH (major contradiction)
   - conflicting_answers: Array of {{"answer_id": "...", "snippet": "relevant quote"}}
   - description: Clear explanation of the contradiction

3. Assess overall consistency (CONSISTENT, MINOR_ISSUES, SIGNIFICANT_CONTRADICTIONS)

4. Rate your confidence in the detection (0.0-1.0)

**Rules**:
- Only flag clear contradictions, not minor wording differences
- Consider context - answers may complement rather than contradict
- FACTUAL contradictions are most serious (typically MEDIUM/HIGH severity)
- TIMELINE/ROLE/SCOPE may be LOW severity if context explains the difference
- If no contradictions found, return empty array

Return JSON with structure:
{{
    "contradictions": [
        {{
            "type": "FACTUAL",
            "severity": "HIGH",
            "conflicting_answers": [
                {{"answer_id": "ans_1", "snippet": "I used Redis"}},
                {{"answer_id": "ans_2", "snippet": "We used Memcached"}}
            ],
            "description": "Technology choice contradicted between answers"
        }}
    ],
    "overall_consistency": "Assessment of consistency across all answers",
    "confidence": 0.85
}}
"""
        return prompt

    def _validate_contradiction(self, contradiction_data: dict, answers: list[dict]) -> bool:
        """Validate contradiction data."""
        # Check required fields
        required_fields = ["type", "severity", "conflicting_answers", "description"]
        if not all(field in contradiction_data for field in required_fields):
            return False

        # Check type
        valid_types = {"FACTUAL", "TIMELINE", "ROLE", "SCOPE"}
        if contradiction_data["type"] not in valid_types:
            return False

        # Check severity
        valid_severities = {"LOW", "MEDIUM", "HIGH"}
        if contradiction_data["severity"] not in valid_severities:
            return False

        # Check conflicting_answers
        conflicting_answers = contradiction_data.get("conflicting_answers", [])
        if len(conflicting_answers) < 2:
            return False

        # Verify answer_ids exist
        answer_ids = {answer.get("answer_id") for answer in answers}
        for conflict in conflicting_answers:
            if conflict.get("answer_id") not in answer_ids:
                return False

        # Check description length
        if len(contradiction_data.get("description", "").strip()) < 10:
            return False

        return True

    def _generate_clarification_question(
        self,
        contradiction_data: dict,
        verification_point: dict,
    ) -> str:
        """Generate clarification question for contradiction."""
        contradiction_type = contradiction_data.get("type", "FACTUAL")
        description = contradiction_data.get("description", "")
        aspect = verification_point.get("aspect", "")

        # Template based on contradiction type
        templates = {
            "FACTUAL": (
                f"I noticed some inconsistency regarding {aspect}. "
                f"{description} Could you clarify which information is accurate?"
            ),
            "TIMELINE": (
                f"There seems to be some timeline inconsistency about {aspect}. "
                f"{description} Could you clarify the exact timeline?"
            ),
            "ROLE": (
                f"I'd like to understand your role better in {aspect}. "
                f"{description} Could you clarify your specific contributions?"
            ),
            "SCOPE": (
                f"I want to make sure I understand the scope of {aspect}. "
                f"{description} Could you clarify the actual scope?"
            ),
        }

        return templates.get(contradiction_type, f"Could you clarify: {description}")
