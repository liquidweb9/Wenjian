"""Generate coaching feedback for the candidate."""

from app.interview.coaching import merge_coaching_with_evidence
from app.interview.schemas import AnswerCoaching
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

COACHING_PROMPT = """You are an interview coach. Provide detailed feedback on the candidate's answer.

For each answer, analyze:
A) What the question was testing — the core knowledge/skill the interviewer aimed to verify
B) What a strong answer includes — the key technical points, design decisions, edge cases, and tradeoffs
C) How the candidate's answer compares — what they did well, what they missed

Rules:
1. Only reference facts the candidate explicitly stated as "confirmed_candidate_facts".
2. Mark suggestions that need confirmation as "requires_candidate_confirmation".
3. Mark general technical content as "generic_technical_content".
4. Do NOT fabricate metrics, incidents, or personal contributions for the candidate.
5. Provide a concise, complete, and expert version of a good answer.
6. Identify knowledge gaps and likely follow-up questions.
7. In question_analysis, explain what the interviewer was trying to verify and what a good answer demonstrates."""


async def generate_coaching_node(state: InterviewState) -> dict:
    """Generate coaching for the latest Q&A."""
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    evaluations = state.get("evaluations", [])

    if not questions or not answers:
        return {}

    latest_q = questions[-1]
    latest_a = answers[-1]
    latest_eval = evaluations[-1] if evaluations else {}

    try:
        llm = AgnesGateway()
        coaching = await llm.generate_structured(
            task_name="coaching",
            system_prompt=COACHING_PROMPT,
            user_payload={
                "question": latest_q.get("question_text", ""),
                "answer": latest_a.get("answer_text", ""),
                "evaluation": {
                    "strengths": latest_eval.get("strengths", []),
                    "factual_errors": latest_eval.get("factual_errors", []),
                    "key_missing_points": latest_eval.get("key_missing_points", []),
                },
            },
            output_model=AnswerCoaching,
            model_tier=get_tier("coaching"),
        )

        result = merge_coaching_with_evidence(
            coaching.model_dump(mode="json"),
            latest_eval,
            state.get("analyses", [])[-1] if state.get("analyses") else None,
        )
        logger.info("coaching_generated")
        return {"latest_coaching": result}

    except Exception as e:
        logger.error("coaching_failed", error=str(e))
        return {
            "latest_coaching": merge_coaching_with_evidence(
                None,
                latest_eval,
                state.get("analyses", [])[-1] if state.get("analyses") else None,
            )
        }
