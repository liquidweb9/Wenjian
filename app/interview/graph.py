"""Main LangGraph interview workflow definition."""

from langgraph.graph import StateGraph, START

from app.interview.state import InterviewState
from app.interview.nodes.initialize import initialize_node
from app.interview.nodes.build_plan import build_plan_node
from app.interview.nodes.select_target import select_target_node
from app.interview.nodes.generate_question import generate_question_node
from app.interview.nodes.wait_for_answer import wait_for_answer
from app.interview.nodes.analyze_answer import analyze_answer_node
from app.interview.nodes.score_answer import score_answer_node
from app.interview.nodes.update_evidence import update_evidence_node
from app.interview.nodes.decide_next import decide_next_node
from app.interview.nodes.generate_coaching import generate_coaching_node
from app.interview.nodes.generate_report import generate_report_node
from app.interview.routing import route_after_select, route_after_decide
from app.persistence.checkpoint import create_checkpointer


def build_interview_graph():
    """Build the LangGraph interview workflow with checkpointer."""
    builder = StateGraph(InterviewState)

    # Add all nodes
    builder.add_node("initialize", initialize_node)
    builder.add_node("build_plan", build_plan_node)
    builder.add_node("select_target", select_target_node)
    builder.add_node("generate_question", generate_question_node)
    builder.add_node("wait_for_answer", wait_for_answer)
    builder.add_node("analyze_answer", analyze_answer_node)
    builder.add_node("score_answer", score_answer_node)
    builder.add_node("update_evidence", update_evidence_node)
    builder.add_node("decide_next", decide_next_node)
    builder.add_node("generate_coaching", generate_coaching_node)
    builder.add_node("generate_report", generate_report_node)

    # Edges
    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "build_plan")
    builder.add_edge("build_plan", "select_target")
    builder.add_conditional_edges("select_target", route_after_select)
    builder.add_edge("generate_question", "wait_for_answer")
    builder.add_edge("wait_for_answer", "analyze_answer")
    builder.add_edge("analyze_answer", "score_answer")
    builder.add_edge("score_answer", "update_evidence")
    builder.add_edge("update_evidence", "generate_coaching")
    builder.add_edge("generate_coaching", "decide_next")
    builder.add_conditional_edges("decide_next", route_after_decide)
    builder.add_edge("generate_report", "__end__")

    checkpointer = create_checkpointer()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["wait_for_answer"])


# Graph instance
interview_graph = build_interview_graph()
