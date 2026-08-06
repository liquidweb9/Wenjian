"""Analyze candidate answer using LLM."""

from app.interview.schemas import AnswerAnalysis
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

ANALYZER_PROMPT = """你是一位面试回答分析器，负责分析候选人针对技术问题的回答。

重点关注：
1. 候选人在回答中提出了哪些主张？
2. 他们提到了哪些技术要点？
3. 回答是否体现了个人贡献，而非模糊的团队表述？
4. 哪些预期要点被覆盖、部分覆盖或遗漏？
5. 是否存在模糊表述、可能的错误或矛盾？
6. 回答的相关性与信息密度如何？
7. 合适的追问目标是什么？

保持客观，不要因语言流畅度而加分或扣分。所有自然语言内容请使用简体中文。"""


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
