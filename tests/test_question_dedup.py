"""Tests for interview question dedup logic."""

from app.interview.nodes.generate_question import (
    _fallback_question,
    _is_duplicate,
    _normalize_text,
    _similarity,
    _suggest_angles,
)
from app.interview.schemas import InterviewQuestion


class TestSimilarity:
    def test_identical_texts(self):
        assert _similarity("hello world", "hello world") == 1.0

    def test_whitespace_insensitive(self):
        assert _similarity("hello  world", "hello world") == 1.0

    def test_punctuation_insensitive(self):
        assert _similarity("你好，世界。", "你好世界") == 1.0

    def test_fully_different(self):
        assert _similarity("apple pie", "rocket science") < 0.5

    def test_normalize_removes_whitespace(self):
        assert _normalize_text("A B   C") == "abc"


class TestIsDuplicate:
    def test_no_previous_returns_false(self):
        assert _is_duplicate("any question", []) is False

    def test_exact_match_is_duplicate(self):
        q = "在Auto-PDP项目中，请说明Planner、Evaluator、Executor三层的职责与交互"
        assert _is_duplicate(q, [q]) is True

    def test_near_identical_is_duplicate(self):
        q1 = "请说明Auto-PDP项目中Planner、Evaluator、Executor三层的职责和交互方式"
        q2 = "在Auto-PDP项目中，请说明Planner、Evaluator、Executor三层各自承担的职责以及它们之间是如何交互的"
        assert _is_duplicate(q2, [q1]) is True

    def test_different_question_not_duplicate(self):
        q1 = "请介绍Auto-PDP项目的整体架构"
        q2 = "描述一次线上故障，说明你是如何定位和修复的"
        assert _is_duplicate(q2, [q1]) is False


class TestSuggestAngles:
    def test_returns_candidates(self):
        angles = _suggest_angles(["基础问题"])
        assert len(angles) > 0
        assert all(isinstance(a, str) for a in angles)

    def test_excludes_used_angles(self):
        prev = ["描述一次真实遇到过的故障，说明根因和修复方式"]
        angles = _suggest_angles(prev)
        assert not any("故障" in a for a in angles)


class TestFallbackQuestion:
    def test_generates_question(self):
        q = _fallback_question(
            project_entry={"title": "Auto-PDP"},
            topic={"name": "Auto-PDP"},
            claim_id="c1",
            topic_id="t1",
            depth=4,
            previous_questions=[],
        )
        assert isinstance(q, InterviewQuestion)
        assert "Auto-PDP" in q.question_text

    def test_avoids_duplicates(self):
        prev = [
            "关于“Auto-PDP”这个项目，请描述这个项目交付过程中遇到的最棘手的一个技术问题，以及你当时是如何定位和解决的。",
            "关于“Auto-PDP”这个项目，请对比这个项目里你考虑过但最终放弃的一个备选方案，说明权衡的过程和放弃的理由。",
            "关于“Auto-PDP”这个项目，请说明这个项目在高并发或大数据量场景下哪里会先成为瓶颈，以及你做过哪些针对性优化。",
            "关于“Auto-PDP”这个项目，请描述一次线上故障或数据不一致事件，复盘根因、影响范围和你采取的措施。",
        ]
        q = _fallback_question(
            project_entry={"title": "Auto-PDP"},
            topic={"name": "Auto-PDP"},
            claim_id="c1",
            topic_id="t1",
            depth=5,
            previous_questions=prev,
        )
        assert not _is_duplicate(q.question_text, prev)
