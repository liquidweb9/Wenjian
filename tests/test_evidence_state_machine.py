"""Tests for Evidence State Machine."""

import pytest

from app.evidence.state_machine import (
    EvidenceState,
    ReasonCode,
    TransitionContext,
    EvidenceStateMachine,
)


class TestEvidenceStateMachine:
    """Test evidence state machine transitions."""

    def test_unseen_to_addressed(self):
        """UNSEEN → ADDRESSED when question asked."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_question=True,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.UNSEEN,
            EvidenceState.ADDRESSED,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.FIRST_INQUIRY

    def test_unseen_to_addressed_blocked_without_question(self):
        """UNSEEN → ADDRESSED blocked without question."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_question=False,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.UNSEEN,
            EvidenceState.ADDRESSED,
            context,
        )

        assert allowed is False
        assert "Guard conditions not met" in msg

    def test_addressed_to_partially_supported(self):
        """ADDRESSED → PARTIALLY_SUPPORTED when answer provided."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_relevant_answer=True,
            strength=0.5,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.ADDRESSED,
            EvidenceState.PARTIALLY_SUPPORTED,
            context,
        )

        assert allowed is True
        assert reason in (ReasonCode.HAS_ANSWER, ReasonCode.EVIDENCE_PROVIDED)

    def test_partially_supported_to_verified(self):
        """PARTIALLY_SUPPORTED → VERIFIED with evidence spans."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_evidence_spans=True,
            strength=0.8,
            confidence="HIGH",
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.PARTIALLY_SUPPORTED,
            EvidenceState.VERIFIED,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.EVIDENCE_SPANS_FOUND

    def test_partially_supported_to_verified_blocked_low_strength(self):
        """PARTIALLY_SUPPORTED → VERIFIED blocked with low strength."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_evidence_spans=True,
            strength=0.5,  # Too low
            confidence="LOW",
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.PARTIALLY_SUPPORTED,
            EvidenceState.VERIFIED,
            context,
        )

        assert allowed is False

    def test_partially_supported_to_verified_blocked_no_spans(self):
        """PARTIALLY_SUPPORTED → VERIFIED blocked without evidence spans."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_evidence_spans=False,  # No spans
            strength=0.9,
            confidence="HIGH",
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.PARTIALLY_SUPPORTED,
            EvidenceState.VERIFIED,
            context,
        )

        assert allowed is False

    def test_addressed_to_unsupported(self):
        """ADDRESSED → UNSUPPORTED when no evidence."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            no_supporting_evidence=True,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.ADDRESSED,
            EvidenceState.UNSUPPORTED,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.NO_EVIDENCE

    def test_partially_supported_to_contradictory(self):
        """PARTIALLY_SUPPORTED → CONTRADICTORY when contradiction detected."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            has_contradiction=True,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.PARTIALLY_SUPPORTED,
            EvidenceState.CONTRADICTORY,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.CONTRADICTION_DETECTED

    def test_contradictory_to_needs_clarification(self):
        """CONTRADICTORY → NEEDS_CLARIFICATION when question generated."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            clarification_question_generated=True,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.CONTRADICTORY,
            EvidenceState.NEEDS_CLARIFICATION,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.CLARIFICATION_NEEDED

    def test_needs_clarification_to_partially_supported(self):
        """NEEDS_CLARIFICATION → PARTIALLY_SUPPORTED after clarification."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            clarification_provided=True,
            has_contradiction=False,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.NEEDS_CLARIFICATION,
            EvidenceState.PARTIALLY_SUPPORTED,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.CLARIFIED

    def test_needs_clarification_to_verified(self):
        """NEEDS_CLARIFICATION → VERIFIED with strong clarification."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            clarification_provided=True,
            has_contradiction=False,
            has_evidence_spans=True,
            strength=0.85,
        )

        allowed, reason, msg = sm.can_transition(
            EvidenceState.NEEDS_CLARIFICATION,
            EvidenceState.VERIFIED,
            context,
        )

        assert allowed is True
        assert reason == ReasonCode.CLARIFIED

    def test_invalid_transition(self):
        """Invalid transitions are rejected."""
        sm = EvidenceStateMachine()

        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
        )

        # UNSEEN → VERIFIED is not allowed
        allowed, reason, msg = sm.can_transition(
            EvidenceState.UNSEEN,
            EvidenceState.VERIFIED,
            context,
        )

        assert allowed is False
        assert "No transition path" in msg

    def test_get_allowed_transitions(self):
        """Get allowed transitions from a state."""
        sm = EvidenceStateMachine()

        # From UNSEEN
        next_states = sm.get_allowed_transitions(EvidenceState.UNSEEN)
        assert EvidenceState.ADDRESSED in next_states

        # From ADDRESSED
        next_states = sm.get_allowed_transitions(EvidenceState.ADDRESSED)
        assert EvidenceState.PARTIALLY_SUPPORTED in next_states
        assert EvidenceState.UNSUPPORTED in next_states

        # From PARTIALLY_SUPPORTED
        next_states = sm.get_allowed_transitions(EvidenceState.PARTIALLY_SUPPORTED)
        assert EvidenceState.VERIFIED in next_states
        assert EvidenceState.CONTRADICTORY in next_states
        assert EvidenceState.UNSUPPORTED in next_states


class TestStateMachineValidation:
    """Test state machine validation."""

    def test_state_machine_is_valid(self):
        """State machine passes validation."""
        sm = EvidenceStateMachine()

        is_valid, issues = sm.validate_state_machine()

        # Print issues for debugging
        if not is_valid:
            print("Validation issues:", issues)

        assert is_valid is True
        assert len(issues) == 0

    def test_all_states_reachable(self):
        """All states are reachable from UNSEEN."""
        sm = EvidenceStateMachine()

        # Manually check reachability
        reachable = {EvidenceState.UNSEEN}
        queue = [EvidenceState.UNSEEN]

        while queue:
            state = queue.pop(0)
            next_states = sm.get_allowed_transitions(state)
            for next_state in next_states:
                if next_state not in reachable:
                    reachable.add(next_state)
                    queue.append(next_state)

        # All states should be reachable
        all_states = set(EvidenceState)
        unreachable = all_states - reachable

        assert len(unreachable) == 0, f"Unreachable states: {unreachable}"


class TestTransitionContext:
    """Test transition context."""

    def test_context_creation(self):
        """Create transition context."""
        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
            answer_id="ans_1",
            has_question=True,
            strength=0.8,
        )

        assert context.verification_point_id == "vp_1"
        assert context.has_question is True
        assert context.strength == 0.8

    def test_context_defaults(self):
        """Context has sensible defaults."""
        context = TransitionContext(
            verification_point_id="vp_1",
            interview_id="int_1",
        )

        assert context.has_question is False
        assert context.strength == 0.0
        assert context.confidence == "LOW"
