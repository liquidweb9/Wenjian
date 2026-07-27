"""Score candidate answer using LLM with rubric."""

from app.interview.rubrics import DIMENSION_DESCRIPTIONS, DIMENSION_WEIGHTS
from app.interview.schemas import AnswerEvaluation
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

SCORER_PROMPT = """You are a technical interview scorer. Score the candidate's answer across multiple dimensions.

Rules:
1. Base scoring ONLY on the question, answer, rubric, and confirmed evidence.
2. Do NOT increase technical score for fluent language.
3. Do NOT deduct for answers that differ from reference answers.
4. Each score must cite specific evidence from the answer.
5. Reduce confidence when uncertain.
6. Do NOT fabricate details the candidate didn't say.
7. Score only the project asked about. Extra descriptions of unrelated projects do not earn points and reduce clarity/relevance when they avoid the target.
8. Listing technologies or restating resume bullets is not implementation depth. Scores above 85 require concrete mechanisms, constraints, failure cases, or debugging evidence.
9. Architecture tradeoff scores above 80 require an explicit comparison between alternatives and a reason for the chosen option.
10. Personal contribution scores above 85 require clear ownership boundaries, collaborators, and what the candidate personally decided or implemented.
11. Production awareness scores above 85 require concrete operational evidence such as measured load/latency, incidents, monitoring thresholds, rollback, capacity, or security handling.
12. Unsupported metrics, unverified improvements, and plausible-sounding claims must not be treated as confirmed achievements.
13. A possible ambiguity or unusual business rule is NOT a factual error. Put it in a
    missing point or follow-up unless the answer is demonstrably technically false.
14. Technical correctness above 90 requires correctness that can be established from
    the answer, not merely a plausible architecture. Do not use 95/100 as a default
    for answers that are generally reasonable.

Scoring dimensions:
- technical_correctness (25%): Is the answer technically correct?
- implementation_depth (20%): Does it show deep implementation understanding?
- architecture_tradeoffs (15%): Does it show architecture awareness and tradeoff thinking?
- personal_contribution (15%): Is the candidate's role clear vs. team?
- production_awareness (15%): Does it consider exceptions, perf, security?
- clarity (10%): Is the answer clear and structured?"""


async def score_answer_node(state: InterviewState) -> dict:
    """Score the latest answer."""
    analyses = state.get("analyses", [])
    answers = state.get("answers", [])
    current_q = state.get("current_question", {})

    if not analyses:
        return {}

    latest_analysis = analyses[-1]
    latest_answer = answers[-1] if answers else {}

    try:
        llm = AgnesGateway()
        evaluation = await llm.generate_structured(
            task_name="answer_scoring",
            system_prompt=SCORER_PROMPT,
            user_payload={
                "question": current_q.get("question_text", ""),
                "answer": latest_answer.get("answer_text", ""),
                "analysis": latest_analysis,
                "target_topic_id": current_q.get("topic_id"),
                "target_claim_id": current_q.get("claim_id"),
                "expected_points": current_q.get("expected_points", []),
                "dimensions": [
                    {"name": d, "weight": w, "description": DIMENSION_DESCRIPTIONS.get(d, "")}
                    for d, w in DIMENSION_WEIGHTS.items()
                ],
            },
            output_model=AnswerEvaluation,
            model_tier=get_tier("answer_scoring"),
        )

        # Calculate weighted total (code, not LLM)
        weighted_total = 0
        for dim in evaluation.dimensions:
            weight = DIMENSION_WEIGHTS.get(dim.dimension, 0)
            weighted_total += dim.score * weight / 100

        logger.info("answer_scored", total=weighted_total, confidence=evaluation.evaluation_confidence)

        return {
            "evaluations": [*state.get("evaluations", []), evaluation.model_dump(mode="json")],
        }

    except Exception as e:
        logger.error("scoring_failed", error=str(e))
        # Don't generate fake scores - mark as retry needed
        return {
            "evaluations": [*state.get("evaluations", []), {
                "dimensions": [],
                "strengths": [],
                "factual_errors": [],
                "demonstrated_level": "unknown",
                "evaluation_confidence": 0.0,
                "model_recommended_action": "follow_up",
                "model_recommended_depth": 1,
            }],
        }
