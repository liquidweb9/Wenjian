"""Project-centered interview planning tests."""

from app.interview.nodes.build_plan import _project_plan


def test_plan_groups_multiple_claims_into_one_project_topic():
    profile = {
        "projects": [
            {"entry_id": "project-a", "title": "Agent Platform"},
            {"entry_id": "project-b", "title": "Video Pipeline"},
        ],
        "experiences": [],
        "research": [],
    }
    claims = [
        {"claim_id": "c1", "entry_id": "project-a", "priority": 90},
        {"claim_id": "c2", "entry_id": "project-a", "priority": 80},
        {"claim_id": "c3", "entry_id": "project-b", "priority": 70},
    ]

    plan = _project_plan(profile, claims, "Backend Engineer", 10)

    assert len(plan.topics) == 2
    assert plan.topics[0].name == "Agent Platform"
    assert plan.topics[0].related_claim_ids == ["c1", "c2"]
    assert plan.topics[1].name == "Video Pipeline"
    assert plan.topics[1].related_claim_ids == ["c3"]
    assert sum(topic.weight for topic in plan.topics) == 100


def test_plan_does_not_create_topics_for_claims_without_project_entry():
    profile = {
        "projects": [{"entry_id": "project-a", "title": "Agent Platform"}],
        "experiences": [],
        "research": [],
    }
    claims = [
        {"claim_id": "c1", "entry_id": "project-a", "priority": 90},
        {"claim_id": "orphan", "entry_id": "missing", "priority": 100},
    ]

    plan = _project_plan(profile, claims, "Backend Engineer", 10)

    assert len(plan.topics) == 1
    assert plan.topics[0].related_claim_ids == ["c1"]
