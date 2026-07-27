"""Tests for interview workflow nodes — rule engine and edge cases."""

import pytest
from app.interview.rules import (
    has_contradiction, current_claim_is_verified,
    all_high_priority_covered, questions_for_current_claim, Decision,
)
from app.interview.routing import route_after_select, route_after_decide
from app.core.enums import NextAction, ClaimStatusEnum


# ---------------------------------------------------------------------------
# Decision class
# ---------------------------------------------------------------------------

class TestDecision:
    def test_create_decision(self):
        d = Decision(action="follow_up", reason="test", target="claim_1", depth=3)
        assert d.action == "follow_up"
        assert d.reason == "test"
        assert d.target == "claim_1"
        assert d.depth == 3

    def test_decision_defaults(self):
        d = Decision(action="finish", reason="done")
        assert d.target == ""
        assert d.depth == 1


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

class TestContradiction:
    def test_no_contradiction_empty(self):
        assert not has_contradiction({"contradictions": []})

    def test_no_contradiction_resolved(self):
        assert not has_contradiction({
            "contradictions": [{"resolved": True}, {"resolved": True}]
        })

    def test_has_unresolved(self):
        assert has_contradiction({
            "contradictions": [{"resolved": False}]
        })

    def test_mixed_resolved_unresolved(self):
        assert has_contradiction({
            "contradictions": [{"resolved": True}, {"resolved": False}]
        })


class TestClaimVerification:
    def test_not_verified_untouched(self):
        assert not current_claim_is_verified({
            "current_claim_id": "c1",
            "claim_statuses": {"c1": {"status": "UNTOUCHED"}},
        })

    def test_verified(self):
        assert current_claim_is_verified({
            "current_claim_id": "c1",
            "claim_statuses": {"c1": {"status": "VERIFIED"}},
        })

    def test_unsupported_counts_as_done(self):
        assert current_claim_is_verified({
            "current_claim_id": "c1",
            "claim_statuses": {"c1": {"status": "UNSUPPORTED"}},
        })

    def test_skipped_counts_as_done(self):
        assert current_claim_is_verified({
            "current_claim_id": "c1",
            "claim_statuses": {"c1": {"status": "SKIPPED"}},
        })

    def test_no_claim_id(self):
        assert not current_claim_is_verified({
            "current_claim_id": None,
            "claim_statuses": {},
        })


class TestHighPriority:
    def test_all_covered(self):
        state = {
            "resume_claims": [
                {"claim_id": "c1", "priority": 80},
                {"claim_id": "c2", "priority": 90},
            ],
            "claim_statuses": {
                "c1": {"status": ClaimStatusEnum.VERIFIED.value},
                "c2": {"status": ClaimStatusEnum.VERIFIED.value},
            },
        }
        assert all_high_priority_covered(state)

    def test_one_uncovered(self):
        state = {
            "resume_claims": [
                {"claim_id": "c1", "priority": 80},
            ],
            "claim_statuses": {
                "c1": {"status": ClaimStatusEnum.UNTOUCHED.value},
            },
        }
        assert not all_high_priority_covered(state)

    def test_low_priority_ignored(self):
        """Claims below priority 70 are ignored."""
        state = {
            "resume_claims": [
                {"claim_id": "c1", "priority": 50},
            ],
            "claim_statuses": {
                "c1": {"status": ClaimStatusEnum.UNTOUCHED.value},
            },
        }
        assert all_high_priority_covered(state)


class TestQuestionCount:
    def test_no_questions(self):
        assert questions_for_current_claim({
            "current_claim_id": "c1",
            "questions": [],
        }) == 0

    def test_count_matching(self):
        assert questions_for_current_claim({
            "current_claim_id": "c1",
            "questions": [
                {"claim_id": "c1"},
                {"claim_id": "c1"},
                {"claim_id": "c2"},
            ],
        }) == 2

    def test_no_claim_id(self):
        assert questions_for_current_claim({
            "current_claim_id": None,
            "questions": [{"claim_id": "c1"}],
        }) == 0


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

class TestRouteAfterSelect:
    def test_normal_routes_to_generate(self):
        result = route_after_select({"next_action": NextAction.FOLLOW_UP.value})
        assert result == "generate_question"

    def test_finish_routes_to_report(self):
        result = route_after_select({"next_action": NextAction.FINISH.value})
        assert result == "generate_report"


class TestRouteAfterDecide:
    def test_follow_up(self):
        assert route_after_decide({"next_action": "follow_up"}) == "generate_question"

    def test_clarify(self):
        assert route_after_decide({"next_action": "clarify"}) == "generate_question"

    def test_increase_difficulty(self):
        assert route_after_decide({"next_action": "increase_difficulty"}) == "generate_question"

    def test_switch_claim(self):
        assert route_after_decide({"next_action": "switch_claim"}) == "select_target"

    def test_switch_topic(self):
        assert route_after_decide({"next_action": "switch_topic"}) == "select_target"

    def test_coaching(self):
        # Coaching is always generated before decide_next, so coaching action falls through
        assert route_after_decide({"next_action": "coaching"}) == "generate_report"

    def test_finish(self):
        assert route_after_decide({"next_action": "finish"}) == "generate_report"

    def test_unknown_defaults_to_report(self):
        assert route_after_decide({"next_action": None}) == "generate_report"


# ---------------------------------------------------------------------------
# Decide Next — rule logic tests (without async)
# ---------------------------------------------------------------------------

class TestDecideNextLogic:
    """Test the _calculate_total_score helper used by decide_next."""

    def test_empty_dimensions(self):
        from app.interview.nodes.decide_next import _calculate_total_score
        assert _calculate_total_score({"dimensions": []}) == 0.0

    def test_average_calculation(self):
        from app.interview.nodes.decide_next import _calculate_total_score
        score = _calculate_total_score({
            "dimensions": [
                {"score": 80, "dimension": "technical_correctness"},
                {"score": 60, "dimension": "implementation_depth"},
                {"score": 100, "dimension": "architecture_tradeoffs"},
            ]
        })
        # Weighted: (80*25 + 60*20 + 100*15) / (25+20+15) = (2000+1200+1500)/60 = 4700/60 = 78.33
        assert score == 4700.0 / 60.0

    def test_no_dimensions_key(self):
        from app.interview.nodes.decide_next import _calculate_total_score
        assert _calculate_total_score({}) == 0.0
