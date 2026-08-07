"""Score candidate answer using LLM with rubric."""

from app.interview.rubrics import DIMENSION_DESCRIPTIONS, DIMENSION_WEIGHTS
from app.interview.schemas import AnswerEvaluation
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import resolve_tier
from app.observability.logging import logger

SCORER_PROMPT = """你是一位技术面试评分器。从多个维度为候选人的回答打分。

规则：
1. 只能基于问题、回答、评分标准和已确认的证据评分。
2. 不要因为语言流畅而提高技术分。
3. 回答与参考答案不同时不得扣分。
4. 每个分数都必须引用回答中的具体证据。
5. 不确定时降低置信度。
6. 不得编造候选人没有说过的细节。
7. 只评价被问到的项目。无关项目的额外描述不计分，且当它回避目标时会降低清晰度/相关性。
8. 罗列技术栈或复述简历条目不算实现深度。超过 85 分的答案必须包含具体机制、约束、失败案例或调试证据。
9. 架构权衡超过 80 分必须明确对比备选方案并说明选择理由。
10. 个人贡献超过 85 分必须明确职责边界、协作者，以及候选人个人决定或实现了什么。
11. 生产意识超过 85 分必须有可量化的运维证据，如实测负载/延迟、故障事件、监控阈值、回滚、容量或安全处理。
12. 未经验证的指标、无法证实的改进、看似合理的说法都不得当作已确认的成就。
13. 可能的歧义或异常业务规则不是事实错误。除非能明确证明技术上错误，否则归入缺失要点或追问。
14. 技术正确性超过 90 分必须能从回答中确立，而不是仅凭看似合理的架构。不要用 95/100 作为一般合理回答的默认分。

评分维度：
- technical_correctness（25%）：回答在技术上是否正确？
- implementation_depth（20%）：是否体现了深入的理解？
- architecture_tradeoffs（15%）：是否体现架构意识与权衡思维？
- personal_contribution（15%）：候选人的角色是否清晰，区别于团队？
- production_awareness（15%）：是否考虑异常、性能、安全、运维？
- clarity（10%）：表达是否清晰、结构化？

所有自然语言内容请使用简体中文。"""

_DIMENSION_NAME_FIELDS = frozenset(DIMENSION_WEIGHTS.keys())
_DIMENSION_FIELD_KEYS = frozenset(
    {"max_score", "reason", "answer_evidence", "missing_points", "confidence"}
)


def _repair_dimensions(parsed: dict) -> dict:
    """Restore dimension objects flattened by the LLM.

    The LLM occasionally emits the `dimensions` array with the opening `{` and
    the `"dimension"`/`"score"` fields dropped, e.g.:

        }, "implementation_depth": 20, "max_score": 100, "reason": "...",

    After json-repair rebalances braces this parses as a dict whose keys are the
    dimension name and the value its score. Rewrite such entries back into the
    schema shape so `AnswerEvaluation` validates.
    """
    dims = parsed.get("dimensions")
    if not isinstance(dims, list):
        return parsed

    repaired = []
    for entry in dims:
        if not isinstance(entry, dict) or "dimension" in entry:
            repaired.append(entry)
            continue

        flattened = {}
        for key, value in entry.items():
            if key in _DIMENSION_FIELD_KEYS:
                flattened[key] = value
            elif key in _DIMENSION_NAME_FIELDS:
                flattened["dimension"] = key
                flattened["score"] = value
            else:
                flattened[key] = value
        repaired.append(flattened)

    parsed["dimensions"] = repaired
    return parsed


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
            model_tier=resolve_tier("answer_scoring", state.get("model_tier")),
            repair=_repair_dimensions,
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
        # Don't generate fake scores - mark as failed so the UI can distinguish
        # "still organizing" from "scoring genuinely failed".
        return {
            "evaluations": [*state.get("evaluations", []), {
                "dimensions": [],
                "strengths": [],
                "factual_errors": [],
                "demonstrated_level": "unknown",
                "evaluation_confidence": 0.0,
                "model_recommended_action": "follow_up",
                "model_recommended_depth": 1,
                "scoring_failed": True,
            }],
        }
