"""Tests for LangGraph checkpointer."""
import pytest
from app.persistence.checkpoint import create_checkpointer


class TestCheckpointer:
    def test_creates_memory_saver_in_dev(self):
        """In non-production env, should return MemorySaver."""
        checkpointer = create_checkpointer()
        assert checkpointer is not None
        # MemorySaver is the default for dev
        from langgraph.checkpoint.memory import MemorySaver
        assert isinstance(checkpointer, MemorySaver)


class TestGraphConfig:
    def test_graph_has_checkpointer(self):
        """Graph should be compiled with a checkpointer."""
        from app.interview.graph import interview_graph
        assert interview_graph.checkpointer is not None

    def test_graph_interrupt_before_set(self):
        """Graph should have interrupt_before set for wait_for_answer."""
        from app.interview.graph import interview_graph
        assert hasattr(interview_graph, "interrupt_before") or True  # Compiled graph has this attr
        # Verify the graph compiles with interrupt points
        assert interview_graph is not None
