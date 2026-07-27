"""Analyze candidate answer using LLM."""

from app.interview.state import InterviewState
from app.interview.schemas import AnswerAnalysis
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

ANALYZER_PROMPT = """You are an interview answer analyzer. Analyze the candidate's answer to a technical question.

Focus on:
1. What claims does the candidate make in their answer?
2. What technical points do they mention?
3. Do they show personal contribution vs. vague team statements?
4. Which expected points did they address, partially address, or miss?
5. Are there vague statements, possible errors, or contradictions?
6. How relevant and information-dense is the answer?
7. What would be a good follow-up target?

Be objective. Do not inflate or penalize based on language fluency."""


async def analyze_answer_node(state: InterviewState) -> dict:
    """Analyze the latest answer."""
    answers = state.get("answers", [])
    if not answers:
        return {"next_action": "finish", "stop_reason": "NO_ANSWER"}

    latest_answer = answers[-1]
    current_q = state.get("current_question", {})
    question_text = current_q.get("question_text", "")

    try:
        llm = AgnesGateway()
        analysis = await llm.generate_structured(
            task_name="answer_analysis",
            system_prompt=ANALYZER_PROMPT,
            user_payload={
                "question": question_text,
                "answer": latest_answer.get("answer_text", ""),
                "expected_points": current_q.get("expected_points", []),
                "strong_signals": current_q.get("strong_signals", []),
            },
            output_model=AnswerAnalysis,
            model_tier=get_tier("answer_analysis"),
        )

        logger.info("answer_analyzed", relevance=analysis.answer_relevance)

        return {
            "analyses": [*state.get("analyses", []), analysis.model_dump(mode="json")],
        }

    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        fallback = AnswerAnalysis(
            answer_summary=latest_answer.get("answer_text", "")[:200],
            answer_relevance=0.5,
        )
        return {
            "analyses": [*state.get("analyses", []), fallback.model_dump(mode="json")],
        }
