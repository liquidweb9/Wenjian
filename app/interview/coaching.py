"""Deterministic coaching fallbacks built from persisted interview evidence."""


def coaching_from_evidence(
    evaluation: dict | None,
    analysis: dict | None,
) -> dict | None:
    if not evaluation and not analysis:
        return None

    evaluation = evaluation or {}
    analysis = analysis or {}
    improvements: list[str] = []

    for point in evaluation.get("key_missing_points", []):
        if point and point not in improvements:
            improvements.append(point)
    for dimension in evaluation.get("dimensions", []):
        for point in dimension.get("missing_points", []):
            if point and point not in improvements:
                improvements.append(point)
    for point in analysis.get("missing_expected_points", []):
        if point and point not in improvements:
            improvements.append(point)

    follow_up = analysis.get("recommended_follow_up_target", "")
    return {
        "score_summary": (
            "本轮评分依据回答中可验证的技术细节、方案取舍、个人贡献和生产证据综合得出。"
        ),
        "what_was_good": evaluation.get("strengths", []),
        "what_to_improve": improvements,
        "likely_follow_up_questions": [follow_up] if follow_up else [],
    }


def merge_coaching_with_evidence(
    coaching: dict | None,
    evaluation: dict | None,
    analysis: dict | None,
) -> dict:
    """Fill structurally valid but empty/incomplete LLM coaching."""
    fallback = coaching_from_evidence(evaluation, analysis) or {}
    result = dict(coaching or {})

    for field in ("score_summary", "what_was_good", "what_to_improve"):
        if not result.get(field):
            result[field] = fallback.get(field, [] if field != "score_summary" else "")
    if not result.get("likely_follow_up_questions"):
        result["likely_follow_up_questions"] = fallback.get(
            "likely_follow_up_questions", []
        )
    return result
