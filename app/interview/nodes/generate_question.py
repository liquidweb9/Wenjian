"""Generate interview question using LLM."""

import difflib
import re
import unicodedata

from app.core.ids import new_question_id
from app.interview.schemas import InterviewQuestion
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.llm.model_router import resolve_tier
from app.llm.token_budget import build_question_context
from app.observability.logging import logger

MAX_DEDUP_RETRIES = 2


def _normalize_text(text: str) -> str:
    """Normalize a question for similarity comparison."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.lower()
    text = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    return text


def _similarity(a: str, b: str) -> float:
    """Char-level similarity ratio between two normalized questions."""
    na, nb = _normalize_text(a), _normalize_text(b)
    if not na and not nb:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def _ngram_similarity(a: str, b: str, n: int = 3) -> float:
    """Jaccard similarity over character n-grams (robust for Chinese)."""
    na, nb = _normalize_text(a), _normalize_text(b)
    if not na and not nb:
        return 1.0
    sa = {na[i : i + n] for i in range(len(na) - n + 1)} if len(na) >= n else {na}
    sb = {nb[i : i + n] for i in range(len(nb) - n + 1)} if len(nb) >= n else {nb}
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 1.0


def _is_duplicate(
    new_text: str,
    previous_texts: list[str],
    ratio_threshold: float = 0.65,
    ngram_threshold: float = 0.5,
) -> bool:
    """True if the new question is identical or near-identical to a previous one.

    Combines a char-level SequenceMatcher ratio with a trigram Jaccard overlap:
    either metric crossing its threshold marks the question as a duplicate. This
    catches both near-verbatim repeats and rewording of the same ask.
    """
    if not previous_texts:
        return False
    for prev in previous_texts:
        if _similarity(new_text, prev) >= ratio_threshold:
            return True
        if _ngram_similarity(new_text, prev) >= ngram_threshold:
            return True
    return False


def _suggest_angles(previous_texts: list[str]) -> list[str]:
    """Suggest concrete new angles based on what has already been asked."""
    all_text = " ".join(_normalize_text(t) for t in previous_texts)
    candidates = [
        ("failure", "描述一次真实遇到过的故障或线上问题，说明根因、排查过程和修复方式", ["故障", "根因", "排查"]),
        ("tradeoff", "对比你当时拒绝的备选方案，说明为什么选择当前实现，代价是什么", ["备选", "放弃", "权衡", "代价"]),
        ("edge_case", "描述一个边界情况或极端输入，你的实现如何处理它", ["边界", "极端", "异常输入"]),
        ("scalability", "当并发量或数据量扩大一个数量级时，你的方案哪里先成为瓶颈，如何扩展", ["瓶颈", "扩展", "并发", "数据量"]),
        ("rollback", "描述一次变更导致问题后，你如何回滚或降级，如何保证数据一致", ["回滚", "降级", "变更"]),
        ("monitoring", "说明该系统在生产中如何监控、告警，以及你如何定位一次真实慢查询", ["监控", "告警", "慢查询", "定位"]),
    ]
    used = {
        key
        for key, _desc, keywords in candidates
        if any(_normalize_text(kw) in all_text for kw in keywords)
    }
    return [desc for key, desc, _kw in candidates if key not in used]

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
8. Never repeat semantically identical questions. The "previous_questions" list is a STRICT BLACKLIST: your new question must be visibly different from every item in it. Repeating, paraphrasing, or re-wording any previous question is a hard failure. Each question must probe a NEW angle: a specific failure scenario, a concrete tradeoff, an edge case, a measurable result, or a design boundary — never re-ask the same ask with a different depth number.
9. If "force_new_angle" is true, you MUST ask about a specific failure case, a concrete design tradeoff, an edge case, or a decision boundary — pick one concrete angle from "suggested_new_angles" if provided.
10. Output strict JSON matching the InterviewQuestion schema."""


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

    previous_questions = [
        q.get("question_text", "") for q in (state.get("questions", [])[-5:])
    ]

    try:
        llm = AgnesGateway()
        question_model = None
        last_error: Exception | None = None

        for attempt in range(MAX_DEDUP_RETRIES + 1):
            is_retry = attempt > 0
            payload = {
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
                "previous_questions": previous_questions,
                "force_new_angle": is_retry,
                "suggested_new_angles": _suggest_angles(previous_questions) if is_retry else [],
            }
            try:
                question_model = await llm.generate_structured(
                    task_name="question_generation",
                    system_prompt=QUESTION_PROMPT,
                    user_payload=payload,
                    output_model=InterviewQuestion,
                    model_tier=resolve_tier("question_generation", state.get("model_tier")),
                )
            except Exception as e:
                last_error = e
                logger.warning("question_generation_failed", error=str(e), attempt=attempt + 1)
                continue

            new_text = question_model.question_text or ""
            if not _is_duplicate(new_text, previous_questions):
                break
            logger.warning(
                "question_duplicate_detected",
                attempt=attempt + 1,
                depth=depth,
                duplicate_of=next(
                    (q for q in previous_questions if _similarity(new_text, q) >= 0.82),
                    "",
                )[:80],
            )
            question_model = None
            if attempt >= MAX_DEDUP_RETRIES:
                break

        if question_model is None and last_error is not None:
            raise last_error

        if question_model is None:
            # Exhausted retries on dedup: accept the last attempt's question is gone,
            # so emit a deterministic fallback that is guaranteed different.
            question_model = _fallback_question(
                project_entry=project_entry,
                topic=topic,
                claim_id=claim_id,
                topic_id=topic_id,
                depth=depth,
                previous_questions=previous_questions,
            )

        question_model.question_id = new_question_id()
        question_model.claim_id = claim_id
        question_model.verification_point_id = vp_id
        question_model.topic_id = topic_id
        question_model.depth = depth

        logger.info("question_generated", question_id=question_model.question_id, depth=depth)

        return {
            "current_question": question_model.model_dump(mode="json"),
            "questions": [*state.get("questions", []), question_model.model_dump(mode="json")],
        }

    except Exception as e:
        logger.error("question_generation_failed", error=str(e))
        # Fallback question
        fallback_q = _fallback_question(
            project_entry=project_entry,
            topic=topic,
            claim_id=claim_id,
            topic_id=topic_id,
            depth=depth,
            previous_questions=previous_questions,
        )
        return {
            "current_question": fallback_q.model_dump(mode="json"),
            "questions": [*state.get("questions", []), fallback_q.model_dump(mode="json")],
        }


def _fallback_question(
    *,
    project_entry: dict,
    topic: dict,
    claim_id: str,
    topic_id: str,
    depth: int,
    previous_questions: list[str],
) -> InterviewQuestion:
    """Build a deterministic fallback question that differs from previous ones."""
    project_name = project_entry.get("title") or topic.get("name") or "这个项目"
    angles = [
        "请描述这个项目交付过程中遇到的最棘手的一个技术问题，以及你当时是如何定位和解决的。",
        "请对比这个项目里你考虑过但最终放弃的一个备选方案，说明权衡的过程和放弃的理由。",
        "请说明这个项目在高并发或大数据量场景下哪里会先成为瓶颈，以及你做过哪些针对性优化。",
        "请描述一次线上故障或数据不一致事件，复盘根因、影响范围和你采取的措施。",
        "请说明你在这个项目里做的关键设计决策，如果重新做一次，哪些地方你会改进、为什么。",
    ]
    base = f"关于“{project_name}”这个项目，{angles[(depth - 1) % len(angles)]}"
    if not _is_duplicate(base, previous_questions):
        return InterviewQuestion(
            question_id=new_question_id(),
            question_text=base,
            topic_id=topic_id,
            claim_id=claim_id,
            depth=depth,
        )
    for angle in angles:
        candidate = f"关于“{project_name}”这个项目，{angle}"
        if not _is_duplicate(candidate, previous_questions):
            return InterviewQuestion(
                question_id=new_question_id(),
                question_text=candidate,
                topic_id=topic_id,
                claim_id=claim_id,
                depth=depth,
            )
    return InterviewQuestion(
        question_id=new_question_id(),
        question_text=f"请从项目目标、整体架构、核心流程和你的职责出发，介绍一下“{project_name}”。",
        topic_id=topic_id,
        claim_id=claim_id,
        depth=depth,
    )
