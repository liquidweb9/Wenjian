"""Scoring rubrics for answer evaluation."""

DIMENSION_WEIGHTS = {
    "technical_correctness": 25,
    "implementation_depth": 20,
    "architecture_tradeoffs": 15,
    "personal_contribution": 15,
    "production_awareness": 15,
    "clarity": 10,
}

DIMENSION_DESCRIPTIONS = {
    "technical_correctness": "是否技术正确，无事实错误",
    "implementation_depth": "能否深入描述实现细节、代码结构、数据流",
    "architecture_tradeoffs": "是否有架构意识和方案权衡能力",
    "personal_contribution": "是否清楚区分个人贡献和团队协作",
    "production_awareness": "是否考虑异常、性能、安全、运维等生产环境因素",
    "clarity": "表达是否清晰、结构化",
}

DEPTH_LEVELS = {
    1: "背景、职责——项目解决什么问题，候选人负责什么",
    2: "执行流程——一次请求如何完整流转",
    3: "代码、接口、数据结构——State字段、节点输入输出、接口契约",
    4: "原理和设计原因——为什么这样拆分",
    5: "边界和故障——超时、重试、幂等、并发、安全",
    6: "替代方案和权衡——为什么不用普通工作流或其他框架",
    7: "反事实和演进——重做会怎么改，规模扩大后怎么办",
}


def calculate_weighted_score(evaluation: dict) -> float:
    """Calculate weighted total score using DIMENSION_WEIGHTS.

    Architecture requirement: backend recalculates weighted score, not LLM.
    """
    dims = evaluation.get("dimensions", [])
    if not dims:
        return 0.0

    total_weight = 0
    weighted_sum = 0
    for d in dims:
        dim_name = d.get("dimension", "")
        weight = DIMENSION_WEIGHTS.get(dim_name, 0)
        score = d.get("score", 0)
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight
