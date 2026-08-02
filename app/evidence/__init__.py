"""Evidence module for Phase 2.

Provides evidence tracking, state machine, span extraction, and contradiction detection.
"""

from app.evidence.state_machine import (
    EvidenceState,
    ReasonCode,
    TransitionContext,
    EvidenceStateMachine,
)
from app.evidence.span_extractor import (
    EvidenceSpan,
    EvidenceSpanExtractor,
    ExtractionResult,
)
from app.evidence.contradiction_detector import (
    Contradiction,
    ContradictionDetector,
    DetectionResult,
)

__all__ = [
    "EvidenceState",
    "ReasonCode",
    "TransitionContext",
    "EvidenceStateMachine",
    "EvidenceSpan",
    "EvidenceSpanExtractor",
    "ExtractionResult",
    "Contradiction",
    "ContradictionDetector",
    "DetectionResult",
]
