"""Generate interview question using LLM."""

from app.core.ids import new_question_id
from app.interview.schemas import InterviewQuestion
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import get_tier
from app.llm.token_budget import build_question_context
from app.observability.logging import logger

QUESTION_PROMPT = """You are a strict but fair technical interviewer. Interview the candidate about a complete resume project, not an isolated technology keyword.

Generate ONE project-centered question. Resume claims and verification points are internal evidence cues, not the subject or wording template of the question.

Rules:
1. One question at a time. No multi-part questions.
2. Keep the project name and goal in context. Ask how the candidate designed, implemented, operated, or improved the project as a coherent system.
3. The first question for a project should establish its goal, architecture, end-to-end flow, and the candidate's responsibility at an appropriate breadth.
4. Later questions should follow the candidate's previous answer and deepen one project decision, failure scenario, tradeoff, or boundary while remaining anchored to that project.
5. Never ask context-free trivia about a framework, library, algorithm, or individual resume bullet.
6. Use all related claims to understand the project; do not generate one question per claim.
7. Do NOT leak expected answers or fabricate project facts.
8. Never repeat semantically identical questions.
9. Output strict JSON matching the InterviewQuestion schema."""


async def generate_question_node(state: InterviewState) -> dict:
    """Generate a question for the current target."""
    claim_id = state.get("current_claim_id")
    vp_id = state.get("current_verification_point_id")
    depth = state.get("current_depth", 1)

    if not claim_id:
        return {"next_action": "finish", "stop_reason": "NO_TARGET"}

    # Find claim
    claim_obj = None
    for rc in state.get("resume_claims", []):
        if rc.get("claim_id") == claim_id:
            claim_obj = rc
            break

    if not claim_obj:
        return {"next_action": "switch_claim", "stop_reason": "CLAIM_NOT_FOUND"}

    entry_id = claim_obj.get("entry_id")
    profile = state.get("resume_profile", {})
    project_entry = next(
        (
            entry
            for section in ("experiences", "projects", "research")
            for entry in profile.get(section, [])
            if entry.get("entry_id") == entry_id
        ),
        {},
    )
    topic = next(
        (
            item
            for item in state.get("interview_plan", {}).get("topics", [])
            if claim_id in item.get("related_claim_ids", [])
        ),
        {},
    )
    related_claims = [
        rc.get("claim_text", "")
        for rc in state.get("resume_claims", [])
        if rc.get("entry_id") == entry_id
    ]
    topic_id = topic.get("topic_id", "")
    project_question_count = sum(
        1
        for question in state.get("questions", [])
        if question.get("topic_id") == topic_id
    )

    # Find verification point
    vp_text = ""
    for vp in claim_obj.get("verification_points", []):
        if vp.get("point_id") == vp_id:
            vp_text = vp.get("description", "")
            break

    # Build context
    context = build_question_context(
        claim_text=claim_obj.get("claim_text", ""),
        source_text=claim_obj.get("claim_text", ""),
        verification_point=vp_text,
        recent_qa=state.get("questions", [])[-3:] if state.get("questions") else None,
    )

    try:
        llm = AgnesGateway()
        question = await llm.generate_structured(
            task_name="question_generation",
            system_prompt=QUESTION_PROMPT,
            user_payload={
                "project": {
                    "title": project_entry.get("title") or topic.get("name"),
                    "organization": project_entry.get("organization"),
                    "role": project_entry.get("role"),
                    "summary": project_entry.get("summary"),
                    "bullets": project_entry.get("bullets", []),
                },
                "related_claims_as_evidence": related_claims,
                "current_evidence_focus": context["claim"],
                "verification_hint": context["verification_point"],
                "is_first_question_for_project": project_question_count == 0,
                "current_depth": depth,
                "previous_questions": [
                    q.get("question_text", "") for q in (state.get("questions", [])[-5:])
                ],
            },
            output_model=InterviewQuestion,
            model_tier=get_tier("question_generation"),
        )

        question.question_id = new_question_id()
        question.claim_id = claim_id
        question.verification_point_id = vp_id
        question.topic_id = topic_id
        question.depth = depth

        logger.info("question_generated", question_id=question.question_id, depth=depth)

        return {
            "current_question": question.model_dump(mode="json"),
            "questions": [*state.get("questions", []), question.model_dump(mode="json")],
        }

    except Exception as e:
        logger.error("question_generation_failed", error=str(e))
        # Fallback question
        fallback_q = InterviewQuestion(
            question_id=new_question_id(),
            question_text=(
                "请从项目目标、整体架构、核心流程和你的职责出发，介绍一下"
                f"“{project_entry.get('title') or topic.get('name') or '这个项目'}”。"
            ),
            topic_id=topic_id,
            claim_id=claim_id,
            depth=depth,
        )
        return {
            "current_question": fallback_q.model_dump(mode="json"),
            "questions": [*state.get("questions", []), fallback_q.model_dump(mode="json")],
        }
