"""Wait for answer - uses LangGraph interrupt."""

from langgraph.types import interrupt
from app.interview.state import InterviewState
from app.core.ids import new_answer_id


async def wait_for_answer(state: InterviewState) -> dict:
    """Interrupt and wait for candidate answer."""
    current_q = state.get("current_question")
    if not current_q:
        return {"next_action": "finish", "stop_reason": "NO_QUESTION"}

    payload = interrupt({
        "type": "interview_question",
        "interview_id": state.get("interview_id", ""),
        "question_id": current_q.get("question_id", ""),
        "question_text": current_q.get("question_text", ""),
    })

    answer_text = str(payload.get("answer_text", "")).strip()
    if not answer_text:
        raise ValueError("answer_text cannot be empty")

    answer = {
        "answer_id": new_answer_id(),
        "question_id": current_q.get("question_id", ""),
        "answer_text": answer_text,
    }

    return {
        "answers": [*state.get("answers", []), answer],
        "turn_count": state.get("turn_count", 0) + 1,
    }
