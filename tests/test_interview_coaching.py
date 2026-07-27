from app.api.v1.interviews import _coaching_from_persisted_evidence
from app.interview.coaching import merge_coaching_with_evidence


def test_persisted_evaluation_produces_visible_coaching():
    coaching = _coaching_from_persisted_evidence(
        {
            "strengths": ["架构描述完整"],
            "key_missing_points": ["缺少方案取舍"],
        },
        {
            "missing_expected_points": ["缺少量化依据"],
            "recommended_follow_up_target": "说明故障恢复过程",
        },
    )

    assert coaching is not None
    assert coaching["what_was_good"] == ["架构描述完整"]
    assert coaching["what_to_improve"] == ["缺少方案取舍", "缺少量化依据"]
    assert coaching["likely_follow_up_questions"] == ["说明故障恢复过程"]


def test_empty_llm_coaching_is_filled_from_scoring_evidence():
    coaching = merge_coaching_with_evidence(
        {
            "score_summary": "",
            "what_was_good": [],
            "what_to_improve": [],
        },
        {
            "strengths": ["路由分层清晰"],
            "key_missing_points": ["缺少灰度与回滚"],
            "dimensions": [
                {"missing_points": ["缺少延迟数据", "缺少灰度与回滚"]}
            ],
        },
        {"recommended_follow_up_target": "说明模型热更新流程"},
    )

    assert coaching["score_summary"]
    assert coaching["what_was_good"] == ["路由分层清晰"]
    assert coaching["what_to_improve"] == ["缺少灰度与回滚", "缺少延迟数据"]
    assert coaching["likely_follow_up_questions"] == ["说明模型热更新流程"]
