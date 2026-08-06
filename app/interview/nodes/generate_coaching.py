"""Generate coaching feedback for the candidate."""

from app.interview.coaching import merge_coaching_with_evidence
from app.interview.schemas import AnswerCoaching
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.observability.logging import logger

COACHING_PROMPT = """你是一位面试教练。针对候选人的回答给出详细反馈。

对每个回答，分析：
A) 问题在考察什么——面试官想验证的核心知识/技能
B) 好的回答包含什么——关键技术点、设计决策、边界情况与权衡
C) 候选人的回答相比如何——哪些做得好，哪些遗漏

规则：
1. 只能引用候选人明确陈述的事实，标记为 "confirmed_candidate_facts"。
2. 需要候选人确认的建议标记为 "requires_candidate_confirmation"。
3. 通用技术内容标记为 "generic_technical_content"。
4. 不得为候选人编造指标、事故或个人贡献。
5. 提供一份简洁、完整、专业的优秀回答版本。
6. 指出知识缺口和可能的追问问题。
7. 在 question_analysis 中解释面试官想验证什么、好的回答应体现什么。

所有自然语言内容请使用简体中文。"""


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
