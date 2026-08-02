"""Evidence State Machine for Phase 2.

Manages evidence state transitions with guard conditions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any


# ============================================================
# States and Reason Codes
# ============================================================

class EvidenceState(str, Enum):
    """Evidence verification states."""

    UNSEEN = "UNSEEN"
    """Initial state - not yet addressed in interview."""

    ADDRESSED = "ADDRESSED"
    """Question asked but no clear answer yet."""

    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    """Some evidence provided but incomplete."""

    VERIFIED = "VERIFIED"
    """Strong evidence with specific spans."""

    UNSUPPORTED = "UNSUPPORTED"
    """Evidence shows claim is not supported."""

    CONTRADICTORY = "CONTRADICTORY"
    """Conflicting evidence detected."""

    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    """Contradiction needs clarification."""


class ReasonCode(str, Enum):
    """Reason codes for state transitions."""

    FIRST_INQUIRY = "FIRST_INQUIRY"
    """First question about this verification point."""

    HAS_ANSWER = "HAS_ANSWER"
    """Relevant answer provided."""

    EVIDENCE_PROVIDED = "EVIDENCE_PROVIDED"
    """Specific evidence provided."""

    EVIDENCE_SPANS_FOUND = "EVIDENCE_SPANS_FOUND"
    """Evidence spans extracted and validated."""

    NO_EVIDENCE = "NO_EVIDENCE"
    """No supporting evidence found."""

    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    """Contradiction with previous evidence."""

    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    """Clarification question generated."""

    CLARIFIED = "CLARIFIED"
    """Clarification provided."""


# ============================================================
# Transition Context
# ============================================================

@dataclass
class TransitionContext:
    """Context for evaluating transition guards."""

    verification_point_id: str
    interview_id: str
    answer_id: str | None = None

    # Guard conditions
    has_question: bool = False
    has_relevant_answer: bool = False
    has_evidence_spans: bool = False
    strength: float = 0.0
    confidence: str = "LOW"
    no_supporting_evidence: bool = False
    has_contradiction: bool = False
    clarification_question_generated: bool = False
    clarification_provided: bool = False

    # Additional data
    evidence_spans: list[dict] | None = None
    contradiction_details: dict | None = None


# ============================================================
# Transition Definition
# ============================================================

@dataclass
class Transition:
    """State transition with guard condition."""

    from_state: EvidenceState
    to_state: EvidenceState
    reason_code: ReasonCode
    guard: Callable[[TransitionContext], bool]
    description: str


# ============================================================
# Evidence State Machine
# ============================================================

class EvidenceStateMachine:
    """Evidence state machine with guard conditions.

    Ensures that evidence state transitions follow business rules
    and cannot be manipulated by direct model output.
    """

    def __init__(self):
        self.transitions = self._define_transitions()

    def _define_transitions(self) -> list[Transition]:
        """Define all allowed transitions with guards."""
        return [
            # UNSEEN → ADDRESSED
            Transition(
                from_state=EvidenceState.UNSEEN,
                to_state=EvidenceState.ADDRESSED,
                reason_code=ReasonCode.FIRST_INQUIRY,
                guard=lambda ctx: ctx.has_question,
                description="First question asked about verification point",
            ),

            # ADDRESSED → PARTIALLY_SUPPORTED
            Transition(
                from_state=EvidenceState.ADDRESSED,
                to_state=EvidenceState.PARTIALLY_SUPPORTED,
                reason_code=ReasonCode.HAS_ANSWER,
                guard=lambda ctx: ctx.has_relevant_answer,
                description="Relevant answer provided with some evidence",
            ),

            # PARTIALLY_SUPPORTED → VERIFIED
            Transition(
                from_state=EvidenceState.PARTIALLY_SUPPORTED,
                to_state=EvidenceState.VERIFIED,
                reason_code=ReasonCode.EVIDENCE_SPANS_FOUND,
                guard=lambda ctx: (
                    ctx.has_evidence_spans and
                    ctx.strength >= 0.7 and
                    ctx.confidence in ("MEDIUM", "HIGH")
                ),
                description="Strong evidence with specific spans extracted",
            ),

            # ADDRESSED → PARTIALLY_SUPPORTED (direct)
            Transition(
                from_state=EvidenceState.ADDRESSED,
                to_state=EvidenceState.PARTIALLY_SUPPORTED,
                reason_code=ReasonCode.EVIDENCE_PROVIDED,
                guard=lambda ctx: ctx.has_relevant_answer and ctx.strength >= 0.4,
                description="Direct evidence provided in answer",
            ),

            # ADDRESSED → UNSUPPORTED
            Transition(
                from_state=EvidenceState.ADDRESSED,
                to_state=EvidenceState.UNSUPPORTED,
                reason_code=ReasonCode.NO_EVIDENCE,
                guard=lambda ctx: ctx.no_supporting_evidence,
                description="No supporting evidence found in answer",
            ),

            # PARTIALLY_SUPPORTED → UNSUPPORTED
            Transition(
                from_state=EvidenceState.PARTIALLY_SUPPORTED,
                to_state=EvidenceState.UNSUPPORTED,
                reason_code=ReasonCode.NO_EVIDENCE,
                guard=lambda ctx: ctx.no_supporting_evidence and ctx.strength < 0.3,
                description="Insufficient evidence after follow-up",
            ),

            # PARTIALLY_SUPPORTED → CONTRADICTORY
            Transition(
                from_state=EvidenceState.PARTIALLY_SUPPORTED,
                to_state=EvidenceState.CONTRADICTORY,
                reason_code=ReasonCode.CONTRADICTION_DETECTED,
                guard=lambda ctx: ctx.has_contradiction,
                description="Contradiction detected with previous evidence",
            ),

            # VERIFIED → CONTRADICTORY
            Transition(
                from_state=EvidenceState.VERIFIED,
                to_state=EvidenceState.CONTRADICTORY,
                reason_code=ReasonCode.CONTRADICTION_DETECTED,
                guard=lambda ctx: ctx.has_contradiction,
                description="New evidence contradicts verified claim",
            ),

            # CONTRADICTORY → NEEDS_CLARIFICATION
            Transition(
                from_state=EvidenceState.CONTRADICTORY,
                to_state=EvidenceState.NEEDS_CLARIFICATION,
                reason_code=ReasonCode.CLARIFICATION_NEEDED,
                guard=lambda ctx: ctx.clarification_question_generated,
                description="Clarification question generated for contradiction",
            ),

            # NEEDS_CLARIFICATION → PARTIALLY_SUPPORTED
            Transition(
                from_state=EvidenceState.NEEDS_CLARIFICATION,
                to_state=EvidenceState.PARTIALLY_SUPPORTED,
                reason_code=ReasonCode.CLARIFIED,
                guard=lambda ctx: ctx.clarification_provided and not ctx.has_contradiction,
                description="Contradiction clarified, returning to partial support",
            ),

            # NEEDS_CLARIFICATION → VERIFIED
            Transition(
                from_state=EvidenceState.NEEDS_CLARIFICATION,
                to_state=EvidenceState.VERIFIED,
                reason_code=ReasonCode.CLARIFIED,
                guard=lambda ctx: (
                    ctx.clarification_provided and
                    not ctx.has_contradiction and
                    ctx.has_evidence_spans and
                    ctx.strength >= 0.7
                ),
                description="Contradiction clarified with strong evidence",
            ),
        ]

    def can_transition(
        self,
        current_state: EvidenceState,
        target_state: EvidenceState,
        context: TransitionContext,
    ) -> tuple[bool, ReasonCode | None, str]:
        """Check if transition is allowed.

        Args:
            current_state: Current evidence state
            target_state: Desired target state
            context: Transition context with guard conditions

        Returns:
            (allowed, reason_code, message)
        """
        # Find matching transitions
        matching_transitions = [
            t for t in self.transitions
            if t.from_state == current_state and t.to_state == target_state
        ]

        if not matching_transitions:
            return False, None, f"No transition path from {current_state} to {target_state}"

        # Check guards
        for transition in matching_transitions:
            try:
                if transition.guard(context):
                    return True, transition.reason_code, transition.description
            except Exception as e:
                # Guard evaluation failed
                return False, None, f"Guard evaluation error: {str(e)}"

        return False, None, f"Guard conditions not met for {current_state} → {target_state}"

    def get_allowed_transitions(
        self,
        current_state: EvidenceState,
    ) -> list[EvidenceState]:
        """Get all possible next states from current state.

        Args:
            current_state: Current evidence state

        Returns:
            List of possible target states
        """
        return list(set(
            t.to_state for t in self.transitions
            if t.from_state == current_state
        ))

    def validate_state_machine(self) -> tuple[bool, list[str]]:
        """Validate state machine completeness.

        Checks:
        - All states are reachable from UNSEEN
        - All states (except UNSEEN) can exit
        - No unreachable states

        Returns:
            (is_valid, issues)
        """
        issues = []
        all_states = set(EvidenceState)

        # Check reachability from UNSEEN
        reachable = {EvidenceState.UNSEEN}
        queue = [EvidenceState.UNSEEN]

        while queue:
            state = queue.pop(0)
            next_states = self.get_allowed_transitions(state)
            for next_state in next_states:
                if next_state not in reachable:
                    reachable.add(next_state)
                    queue.append(next_state)

        unreachable = all_states - reachable
        if unreachable:
            issues.append(f"Unreachable states: {unreachable}")

        # Check exit paths (all states except terminal states should have exits)
        terminal_states = {EvidenceState.VERIFIED, EvidenceState.UNSUPPORTED}
        for state in all_states:
            if state != EvidenceState.UNSEEN and state not in terminal_states:
                next_states = self.get_allowed_transitions(state)
                if not next_states:
                    issues.append(f"State {state} has no exit paths")

        return len(issues) == 0, issues
