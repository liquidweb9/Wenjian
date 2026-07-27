"""Tests for interview workflow."""

import pytest
from app.interview.rules import has_contradiction, current_claim_is_verified, Decision
from app.interview.routing import route_after_decide
from app.core.enums import NextAction


class TestRules:
    def test_no_contradiction(self):
        state = {"contradictions": []}
        assert has_contradiction(state) is False

    def test_unresolved_contradiction(self):
        state = {"contradictions": [{"resolved": False}]}
        assert has_contradiction(state) is True

    def test_resolved_contradiction(self):
        state = {"contradictions": [{"resolved": True}]}
        assert has_contradiction(state) is False

    def test_claim_not_verified(self):
        state = {
            "current_claim_id": "claim_1",
            "claim_statuses": {"claim_1": {"status": "UNTOUCHED"}},
        }
        assert current_claim_is_verified(state) is False

    def test_claim_verified(self):
        state = {
            "current_claim_id": "claim_1",
            "claim_statuses": {"claim_1": {"status": "VERIFIED"}},
        }
        assert current_claim_is_verified(state) is True


class TestRouting:
    def test_finish_routes_to_report(self):
        result = route_after_decide({"next_action": NextAction.FINISH.value})
        assert result == "generate_report"

    def test_follow_up_routes_to_question(self):
        result = route_after_decide({"next_action": NextAction.FOLLOW_UP.value})
        assert result == "generate_question"

    def test_switch_claim_routes_to_select(self):
        result = route_after_decide({"next_action": NextAction.SWITCH_CLAIM.value})
        assert result == "select_target"

    def test_coaching_routes_to_report(self):
        # Coaching is now always generated before decide_next, so coaching action falls through
        result = route_after_decide({"next_action": NextAction.COACHING.value})
        assert result == "generate_report"


class TestDecision:
    def test_decision_creation(self):
        d = Decision("follow_up", reason="test", target="claim_1", depth=3)
        assert d.action == "follow_up"
        assert d.reason == "test"
        assert d.target == "claim_1"
        assert d.depth == 3
