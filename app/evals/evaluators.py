"""LLM-based evaluators for regression testing.

M2.3: Replaces mock evaluators with real LLM calls using versioned prompts and rubrics.
"""

from typing import Any

from app.evals.prompt_registry import get_prompt_registry
from app.evals.rubric_versioning import get_rubric_registry
from app.llm.gateway import AgnesGateway
from app.evals.datasets import NextAction, EvidenceStatus


async def score_answer_with_llm(
    question: str,
    answer: str,
    prompt_version: int | None = None,
    rubric_version: int | None = None,
) -> dict[str, int]:
    """Score an answer using LLM with versioned prompt and rubric.

    Args:
        question: Interview question text
        answer: Candidate's answer text
        prompt_version: Specific prompt version (None = latest)
        rubric_version: Specific rubric version (None = latest)

    Returns:
        Dict with dimension scores: {dimension_name: score}
    """
    prompt_registry = get_prompt_registry()
    rubric_registry = get_rubric_registry()

    # Get prompt and rubric
    prompt_spec = await prompt_registry.get_prompt("score_answer", prompt_version)
    rubric_spec = await rubric_registry.get_rubric("answer_scoring", rubric_version)

    # Build system prompt with rubric information
    system_prompt = prompt_spec.system_prompt

    # Add rubric dimensions
    rubric_text = "\n\n评分维度:\n"
    for dim, weight in rubric_spec.dimension_weights.items():
        desc = rubric_spec.dimension_descriptors.get(dim, "")
        rubric_text += f"- {dim} (权重 {weight}): {desc}\n"

    full_system_prompt = system_prompt + rubric_text

    # Build user message
    user_message = f"""问题: {question}

回答: {answer}

请根据上述评分维度对回答进行评分。"""

    # Call LLM
    gateway = AgnesGateway()
    response = await gateway.complete(
        task_name="score_answer",
        model="gpt-4",
        system_prompt=full_system_prompt,
        user_message=user_message,
        response_format={"type": "json_object"},
    )

    # Parse response - expecting JSON with dimension scores
    import json
    result = json.loads(response)

    # Extract scores
    dimensions = result.get("dimensions", [])
    scores = {}
    for d in dimensions:
        dim_name = d.get("dimension")
        score = d.get("score", 0)
        if dim_name:
            scores[dim_name] = score

    return scores


async def route_decision_with_llm(
    state: dict,
    evaluation: dict,
    prompt_version: int | None = None,
) -> NextAction:
    """Determine next action using LLM with versioned prompt.

    Args:
        state: Interview state dict
        evaluation: Latest evaluation dict
        prompt_version: Specific prompt version (None = latest)

    Returns:
        NextAction enum value
    """
    prompt_registry = get_prompt_registry()
    prompt_spec = await prompt_registry.get_prompt("route_decision", prompt_version)

    # Build context for routing
    context = f"""当前状态:
- 轮次: {state.get('turn_count')}/{state.get('max_turns')}
- 当前Claim: {state.get('current_claim_id')}
- Claim状态: {state.get('claim_status')}
- 当前深度: {state.get('current_depth')}
- 本Claim已问: {state.get('questions_on_claim')} 个问题
- 最新相关性得分: {evaluation.get('dimensions', [{}])[0].get('score', 0)}

最新评估:
- 优势: {evaluation.get('strengths', [])}
- 缺失点: {evaluation.get('key_missing_points', [])}

请决定下一步行动: FOLLOW_UP, CLARIFY, INCREASE_DIFFICULTY, SWITCH_CLAIM, SWITCH_TOPIC, COACHING, FINISH
"""

    gateway = AgnesGateway()
    response = await gateway.complete(
        task_name="route_decision",
        model="gpt-4",
        system_prompt=prompt_spec.system_prompt,
        user_message=context,
        response_format={"type": "json_object"},
    )

    import json
    result = json.loads(response)
    action = result.get("action", "FOLLOW_UP")

    # Validate action
    valid_actions = {"FOLLOW_UP", "CLARIFY", "INCREASE_DIFFICULTY",
                    "SWITCH_CLAIM", "SWITCH_TOPIC", "COACHING", "FINISH"}
    if action not in valid_actions:
        return "FOLLOW_UP"

    return action  # type: ignore


async def evaluate_evidence_with_llm(
    claim: str,
    verification_point: str,
    answer: str,
    previous_status: EvidenceStatus,
    prompt_version: int | None = None,
) -> tuple[EvidenceStatus, int]:
    """Evaluate evidence status using LLM with versioned prompt.

    Args:
        claim: Resume claim text
        verification_point: What aspect is being verified
        answer: Candidate's answer
        previous_status: Previous evidence status
        prompt_version: Specific prompt version (None = latest)

    Returns:
        Tuple of (new_status, strength_score)
    """
    prompt_registry = get_prompt_registry()
    prompt_spec = await prompt_registry.get_prompt("evaluate_evidence", prompt_version)

    context = f"""简历声明: {claim}

验证点: {verification_point}

之前状态: {previous_status}

候选人回答: {answer}

请评估证据状态 (UNTOUCHED, IN_PROGRESS, PARTIALLY_VERIFIED, VERIFIED, CONTRADICTORY, UNSUPPORTED)
以及证据强度 (0-100)。"""

    gateway = AgnesGateway()
    response = await gateway.complete(
        task_name="evaluate_evidence",
        model="gpt-4",
        system_prompt=prompt_spec.system_prompt,
        user_message=context,
        response_format={"type": "json_object"},
    )

    import json
    result = json.loads(response)

    status = result.get("status", "IN_PROGRESS")
    strength = result.get("strength", 50)

    # Validate status
    valid_statuses = {"UNTOUCHED", "IN_PROGRESS", "PARTIALLY_VERIFIED",
                     "VERIFIED", "CONTRADICTORY", "UNSUPPORTED"}
    if status not in valid_statuses:
        status = "IN_PROGRESS"

    return status, strength  # type: ignore
