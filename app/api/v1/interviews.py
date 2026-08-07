"""Interview management API endpoints."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.sse_manager import sse_manager
from app.core.deps import get_current_user
from app.core.enums import NextAction
from app.core.ids import new_answer_id, new_id, new_interview_id, new_question_id, new_thread_id
from app.interview.coaching import coaching_from_evidence
from app.interview.graph import interview_graph
from app.interview.nodes.build_plan import build_plan_node
from app.interview.nodes.initialize import initialize_node
from app.interview.state import InterviewState
from app.observability.logging import logger
from app.persistence.database import get_session
from app.persistence.models import (
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    InterviewReport,
    ResumeClaim,
    ResumeProfile,
    ResumeRevision,
    ResumeSource,
    User,
)
from app.resume.claim_selection import select_core_claims

router = APIRouter(prefix="/interviews", tags=["interviews"])


async def _interview_owned_by(
    session: AsyncSession, interview_id: str, user_id: str
) -> Interview | None:
    """Fetch an interview only if it belongs to the given user (else None)."""
    result = await session.execute(
        select(Interview).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


class CreateInterviewRequest(BaseModel):
    resume_id: str
    resume_revision_id: str
    target_role: str
    job_description: str | None = None
    job_target_id: str | None = None
    mode: str = "simulation"
    max_turns: int = 15
    model_tier: str = "auto"


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer_text: str
    idempotency_key: str | None = None


def _make_event(event_type: str, interview_id: str, thread_id: str, sequence: int, payload: dict) -> dict:
    return {
        "event_id": uuid.uuid4().hex[:16],
        "event_type": event_type,
        "interview_id": interview_id,
        "thread_id": thread_id,
        "sequence": sequence,
        "created_at": datetime.utcnow().isoformat(),
        "payload": payload,
    }


_sequence_counters: dict[str, int] = {}


def _next_seq(interview_id: str) -> int:
    seq = _sequence_counters.get(interview_id, 0) + 1
    _sequence_counters[interview_id] = seq
    return seq


def _coaching_from_persisted_evidence(
    evaluation: dict | None,
    analysis: dict | None,
) -> dict | None:
    """Backward-compatible wrapper used by API history and existing tests."""
    return coaching_from_evidence(evaluation, analysis)


async def _publish(interview_id: str, event_type: str, thread_id: str, payload: dict):
    """Publish SSE event; best-effort — failures are logged, not raised."""
    try:
        seq = _next_seq(interview_id)
        event = _make_event(event_type, interview_id, thread_id, seq, payload)
        await sse_manager.publish(interview_id, event)
    except Exception:
        logger.warning("sse_publish_failed", event_type=event_type, interview_id=interview_id)


async def _ensure_graph_checkpoint(
    interview: Interview,
    session: AsyncSession,
) -> dict:
    """Restore an interrupted interview after the in-memory checkpoint is lost."""
    config = {"configurable": {"thread_id": interview.thread_id}}
    try:
        snapshot = interview_graph.get_state(config)
        if snapshot and snapshot.values and snapshot.values.get("current_question"):
            return snapshot.values
    except Exception:
        pass

    questions_result = await session.execute(
        select(InterviewQuestion)
        .where(InterviewQuestion.interview_id == interview.interview_id)
        .order_by(InterviewQuestion.created_at.asc())
    )
    questions = list(questions_result.scalars().all())
    answers_result = await session.execute(
        select(InterviewAnswer)
        .where(InterviewAnswer.interview_id == interview.interview_id)
        .order_by(InterviewAnswer.created_at.asc())
    )
    answers = list(answers_result.scalars().all())
    answered_question_ids = {answer.question_id for answer in answers}
    current = next(
        (question for question in reversed(questions)
         if question.question_id not in answered_question_ids),
        None,
    )
    if current is None or interview.status == "finished":
        return {}

    profile_result = await session.execute(
        select(ResumeProfile)
        .where(ResumeProfile.resume_id == interview.resume_id)
        .order_by(ResumeProfile.created_at.desc())
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    revision_result = await session.execute(
        select(ResumeRevision)
        .where(ResumeRevision.resume_id == interview.resume_id)
        .order_by(ResumeRevision.created_at.desc())
        .limit(1)
    )
    revision = revision_result.scalar_one_or_none()
    claims_result = await session.execute(
        select(ResumeClaim)
        .where(ResumeClaim.resume_id == interview.resume_id)
        .order_by(ResumeClaim.priority.desc())
    )
    profile_data = profile.data if profile else {}
    claims = select_core_claims(
        [row.data for row in claims_result.scalars().all()],
        profile_data,
    )
    base_state: InterviewState = {
        "interview_id": interview.interview_id,
        "thread_id": interview.thread_id,
        "resume_id": interview.resume_id,
        "resume_revision_id": revision.revision_id if revision else "",
        "target_role": interview.target_role,
        "job_description": interview.job_description,
        "interview_mode": interview.mode,
        "resume_profile": profile_data,
        "resume_claims": claims,
        "interview_plan": {},
        "max_turns": interview.max_turns,
    }
    restored = {**base_state, **await initialize_node(base_state)}
    restored.update(await build_plan_node(restored))
    restored.update({
        "questions": [question.data for question in questions],
        "answers": [
            {
                "answer_id": answer.answer_id,
                "question_id": answer.question_id,
                "answer_text": answer.answer_text,
            }
            for answer in answers
        ],
        "analyses": [answer.analysis or {} for answer in answers],
        "evaluations": [answer.evaluation or {} for answer in answers],
        "turn_count": len(answers),
        "current_question": current.data,
        "current_topic_id": current.data.get("topic_id"),
        "current_claim_id": current.data.get("claim_id"),
        "current_verification_point_id": current.data.get("verification_point_id"),
        "current_depth": current.data.get("depth", 1),
    })
    await interview_graph.aupdate_state(config, restored, as_node="generate_question")
    logger.info(
        "interview_checkpoint_restored",
        interview_id=interview.interview_id,
        question_id=current.question_id,
        answered=len(answers),
    )
    return restored


@router.get("")
async def list_interviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    resume_id: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """List interviews with pagination and filters."""
    base = select(
        Interview.interview_id,
        Interview.thread_id,
        Interview.resume_id,
        Interview.target_role,
        Interview.mode,
        Interview.max_turns,
        Interview.status,
        Interview.created_at,
        Interview.finished_at,
        select(func.count(InterviewAnswer.answer_id))
        .where(InterviewAnswer.interview_id == Interview.interview_id)
        .correlate(Interview)
        .scalar_subquery()
        .label("persisted_turn_count"),
    ).where(Interview.user_id == user.user_id)

    if status:
        base = base.where(Interview.status == status)
    if resume_id:
        base = base.where(Interview.resume_id == resume_id)

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total_r = await session.execute(count_q)
    total = total_r.scalar() or 0

    # Sort
    sort_col = Interview.created_at if sort_by == "created_at" else Interview.status
    if sort_order == "desc":
        base = base.order_by(sort_col.desc())
    else:
        base = base.order_by(sort_col.asc())

    offset = (page - 1) * page_size
    base = base.offset(offset).limit(page_size)

    result = await session.execute(base)
    rows = result.all()

    items = []
    for row in rows:
        # Try to get turn_count from graph state
        turn_count = row[9] or 0
        try:
            gs = interview_graph.get_state({"configurable": {"thread_id": row[1]}})
            if gs and gs.values:
                # MemorySaver state disappears on process restart. Persisted answers
                # remain the durable source and must never be replaced by a stale 0.
                turn_count = max(turn_count, gs.values.get("turn_count", 0) or 0)
        except Exception:
            pass

        items.append({
            "interview_id": row[0],
            "thread_id": row[1],
            "resume_id": row[2],
            "target_role": row[3],
            "mode": row[4],
            "max_turns": row[5],
            "status": row[6],
            "turn_count": turn_count,
            "finished": row[6] == "finished",
            "created_at": row[7].isoformat() if row[7] else None,
            "finished_at": row[8].isoformat() if row[8] else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{interview_id}/events")
async def interview_events(
    interview_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """SSE endpoint — stream interview events to the client."""
    if not await _interview_owned_by(session, interview_id, user.user_id):
        raise HTTPException(status_code=404, detail="Interview not found")
    subscriber_id = uuid.uuid4().hex[:12]
    queue = await sse_manager.subscribe(interview_id, subscriber_id)

    async def event_generator():
        try:
            yield ":ok\n\n"

            # Send state snapshot on connect so late subscribers don't miss events
            try:
                iv_result = await session.execute(
                    select(Interview).where(Interview.interview_id == interview_id)
                )
                interview = iv_result.scalar_one_or_none()
                if interview:
                    thread_id = interview.thread_id
                    try:
                        graph_values = await _ensure_graph_checkpoint(interview, session)
                        current_q = graph_values.get("current_question")
                        finished = graph_values.get("finished", False)

                        # The database is durable while the development graph
                        # checkpointer is not. A completed interview must still
                        # emit a terminal snapshot after a process restart.
                        if interview.status == "finished":
                            answer_count_result = await session.execute(
                                select(func.count(InterviewAnswer.answer_id)).where(
                                    InterviewAnswer.interview_id == interview_id
                                )
                            )
                            persisted_turn_count = answer_count_result.scalar() or 0
                            seq = _next_seq(interview_id)
                            queue.put_nowait(json.dumps(_make_event(
                                "interview.finished", interview_id, thread_id, seq,
                                {"stop_reason": graph_values.get("stop_reason") or "USER_REQUESTED",
                                 "turn_count": max(graph_values.get("turn_count", 0) or 0, persisted_turn_count)},
                            )))
                        elif finished:
                            seq = _next_seq(interview_id)
                            queue.put_nowait(json.dumps(_make_event(
                                "interview.finished", interview_id, thread_id, seq,
                                {"stop_reason": graph_values.get("stop_reason"), "turn_count": graph_values.get("turn_count", 0)},
                            )))
                        elif current_q:
                            seq = _next_seq(interview_id)
                            queue.put_nowait(json.dumps(_make_event(
                                "interview.initialized", interview_id, thread_id, seq,
                                {"interview_id": interview_id, "target_role": interview.target_role, "mode": interview.mode},
                            )))
                            seq = _next_seq(interview_id)
                            queue.put_nowait(json.dumps(_make_event(
                                "question.ready", interview_id, thread_id, seq,
                                {"question_id": current_q.get("question_id"), "question_text": current_q.get("question_text")},
                            )))
                    except Exception:
                        pass  # graph state unavailable, skip snapshot
            except Exception:
                pass  # DB unavailable, skip snapshot

            while True:
                if await request.is_disconnected():
                    break

                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ":heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await sse_manager.unsubscribe(interview_id, subscriber_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("")
async def create_interview(
    body: CreateInterviewRequest,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Create a new interview session."""
    # Verify resume belongs to the current user
    resume_result = await session.execute(
        select(ResumeSource).where(
            ResumeSource.resume_id == body.resume_id,
            ResumeSource.user_id == user.user_id,
        )
    )
    if not resume_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Resume not found")
    # Verify resume is confirmed
    rev_result = await session.execute(
        select(ResumeRevision).where(
            ResumeRevision.revision_id == body.resume_revision_id,
            ResumeRevision.resume_id == body.resume_id,
        )
    )
    rev = rev_result.scalar_one_or_none()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    if rev.status.value != "CONFIRMED":
        raise HTTPException(status_code=400, detail="Resume revision not confirmed")

    # Load profile
    profile_result = await session.execute(
        select(ResumeProfile).where(
            ResumeProfile.resume_id == body.resume_id,
            ResumeProfile.revision_id == body.resume_revision_id,
        )
    )
    profile_row = profile_result.scalar_one_or_none()
    profile_data = profile_row.data if profile_row else {}

    # Load only the bounded, interview-worthy claim set. This also keeps
    # interviews created from legacy 30+ claim profiles manageable.
    claims_result = await session.execute(
        select(ResumeClaim)
        .where(ResumeClaim.resume_id == body.resume_id)
        .order_by(ResumeClaim.priority.desc())
    )
    claims = select_core_claims(
        [row.data for row in claims_result.scalars().all()],
        profile_data,
    )

    # Generate IDs at API level — one consistent thread_id for graph config + business
    interview_id = new_interview_id()
    thread_id = new_thread_id()

    # Initial state with consistent IDs
    initial_state: InterviewState = {
        "interview_id": interview_id,
        "thread_id": thread_id,
        "resume_id": body.resume_id,
        "resume_revision_id": body.resume_revision_id,
        "target_role": body.target_role,
        "job_description": body.job_description,
        "interview_mode": body.mode,
        "model_tier": body.model_tier if body.model_tier in ("fast", "balanced", "judge") else None,
        "resume_profile": profile_data,
        "resume_claims": claims,
        "interview_plan": {},
        "current_topic_id": None,
        "current_claim_id": None,
        "current_verification_point_id": None,
        "current_depth": 1,
        "current_question": None,
        "questions": [],
        "answers": [],
        "analyses": [],
        "evaluations": [],
        "claim_statuses": {},
        "contradictions": [],
        "evidence_items": [],
        "coverage": {},
        "ability_profile": {},
        "turn_count": 0,
        "max_turns": body.max_turns,
        "next_action": None,
        "stop_reason": None,
        "finished": False,
        "latest_coaching": None,
        "final_report": None,
    }

    # Run graph up to first interrupt — thread_id matches interview_id
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = await interview_graph.ainvoke(initial_state, config)
        interview_id = result.get("interview_id", interview_id)
        current_q = result.get("current_question")
    except Exception as e:
        logger.error("interview_start_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")

    # Save interview to DB
    interview = Interview(
        interview_id=interview_id,
        thread_id=thread_id,
        user_id=user.user_id,
        resume_id=body.resume_id,
        job_target_id=body.job_target_id,
        target_role=body.target_role,
        job_description=body.job_description,
        mode=body.mode,
        max_turns=body.max_turns,
        status="in_progress",
    )
    await session.merge(interview)

    # Save the first question to DB
    if current_q:
        db_q = InterviewQuestion(
            question_id=current_q.get("question_id", new_question_id()),
            interview_id=interview_id,
            data=current_q,
        )
        await session.merge(db_q)

    await session.commit()

    # Publish SSE events
    await _publish(interview_id, "interview.initialized", thread_id, {
        "interview_id": interview_id,
        "target_role": body.target_role,
        "mode": body.mode,
    })
    if current_q:
        await _publish(interview_id, "question.ready", thread_id, {
            "question_id": current_q.get("question_id"),
            "question_text": current_q.get("question_text"),
        })

    logger.info("interview_created", interview_id=interview_id, thread_id=thread_id)

    return {
        "interview_id": interview_id,
        "thread_id": thread_id,
        "status": "in_progress",
        "current_question": current_q.get("question_text") if current_q else None,
        "question_id": current_q.get("question_id") if current_q else None,
        "turn_count": 0,
        "max_turns": body.max_turns,
    }


@router.get("/{interview_id}")
async def get_interview(
    interview_id: str,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get interview state."""
    result = await session.execute(
        select(Interview).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user.user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Get current state from graph checkpoint
    thread_id = interview.thread_id
    state = None
    try:
        state = interview_graph.get_state({"configurable": {"thread_id": thread_id}})
    except Exception:
        pass  # Checkpointer might not have this state

    current_question = None
    if state and state.values:
        current_question = state.values.get("current_question")

    # Also try reading from DB for current question
    if not current_question:
        q_result = await session.execute(
            select(InterviewQuestion).where(
                InterviewQuestion.interview_id == interview_id
            ).order_by(InterviewQuestion.created_at.desc()).limit(1)
        )
        last_q = q_result.scalar_one_or_none()
        if last_q:
            current_question = last_q.data

    # Build Q&A history from DB answers matching graph questions. The graph uses an
    # in-memory checkpointer in development, so fall back to persisted questions
    # after a process restart.
    all_questions = state.values.get("questions", []) if state else []
    all_answers = state.values.get("answers", []) if state else []
    db_questions_result = await session.execute(
        select(InterviewQuestion).where(
            InterviewQuestion.interview_id == interview_id
        ).order_by(InterviewQuestion.created_at.asc())
    )
    db_questions = db_questions_result.scalars().all()
    if not all_questions:
        all_questions = [q.data for q in db_questions]
    # Also load answers from DB for robustness
    db_answers_result = await session.execute(
        select(InterviewAnswer).where(
            InterviewAnswer.interview_id == interview_id
        ).order_by(InterviewAnswer.created_at.asc())
    )
    db_answers = db_answers_result.scalars().all()
    db_answers_map = {a.question_id: a for a in db_answers}
    graph_answers_map = {
        answer.get("question_id"): answer
        for answer in all_answers
        if answer.get("question_id")
    }

    history = []
    for q in all_questions:
        qid = q.get("question_id", "")
        db_ans = db_answers_map.get(qid)
        # The next question can exist before its answer, so positional matching
        # can shift or drop history after refresh. question_id is durable.
        ans = graph_answers_map.get(qid)
        answer_text = (ans.get("answer_text") if ans else None) or (db_ans.answer_text if db_ans else None)
        # Filter out fake "[END OF INTERVIEW]" answer
        if answer_text and answer_text.strip() == "[END OF INTERVIEW]":
            continue
        history.append({
            "question_id": qid,
            "question_text": q.get("question_text", ""),
            "answer_text": answer_text,
            "evaluation": db_ans.evaluation if db_ans else None,
            "analysis": db_ans.analysis if db_ans else None,
            "coaching": (
                _coaching_from_persisted_evidence(
                    db_ans.evaluation,
                    db_ans.analysis,
                )
                if db_ans
                else None
            ),
        })

    return {
        "interview_id": interview.interview_id,
        "thread_id": interview.thread_id,
        "resume_id": interview.resume_id,
        "target_role": interview.target_role,
        "mode": interview.mode,
        "status": interview.status,
        "turn_count": max(
            state.values.get("turn_count", 0) if state else 0,
            len(db_answers),
        ),
        "max_turns": interview.max_turns,
        "current_question": current_question,
        "finished": interview.status == "finished" or (
            state.values.get("finished", False) if state else False
        ),
        "stop_reason": state.values.get("stop_reason") if state else None,
        "history": history,
    }


@router.post("/{interview_id}/answers")
async def submit_answer(
    interview_id: str,
    body: SubmitAnswerRequest,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Submit answer to current question and continue interview."""
    result = await session.execute(
        select(Interview).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user.user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "finished":
        raise HTTPException(status_code=400, detail="Interview already finished")

    thread_id = interview.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # Check idempotency
    if body.idempotency_key:
        existing = await session.execute(
            select(InterviewAnswer).where(
                InterviewAnswer.interview_id == interview_id,
                InterviewAnswer.answer_id == body.idempotency_key,
            )
        )
        if existing.scalar_one_or_none():
            logger.info("duplicate_answer_skipped", interview_id=interview_id)
            return {
                "interview_id": interview_id,
                "status": interview.status,
                "duplicate": True,
            }

    # Verify current question matches
    try:
        state = interview_graph.get_state(config)
    except Exception:
        state = None

    if state and state.values:
        current_q = state.values.get("current_question", {})
        expected_qid = current_q.get("question_id", "")
        if expected_qid and body.question_id != expected_qid:
            raise HTTPException(
                status_code=400,
                detail=f"Question ID mismatch. Expected {expected_qid}, got {body.question_id}",
            )
    else:
        restored = await _ensure_graph_checkpoint(interview, session)
        expected_qid = restored.get("current_question", {}).get("question_id", "")
        if expected_qid and body.question_id != expected_qid:
            raise HTTPException(
                status_code=400,
                detail=f"Question ID mismatch. Expected {expected_qid}, got {body.question_id}",
            )

    # Publish answer received
    await _publish(interview_id, "answer.accepted", thread_id, {
        "question_id": body.question_id,
    })

    # Resume graph with answer — stream node updates so staged feedback events
    # (analysis → scoring → evidence → coaching → next question) are published
    # progressively as each node completes, instead of all at the very end.
    try:
        current_q = None
        finished = False
        turn_count = 0
        latest_analysis = None
        latest_eval = None
        latest_coaching = None
        final_report = None

        async for update in interview_graph.astream(
            Command(resume={"answer_text": body.answer_text}),
            config,
            stream_mode="updates",
        ):
            for node_name, node_update in (update or {}).items():
                if node_name == "wait_for_answer":
                    turn_count = node_update.get("turn_count", turn_count)
                elif node_name == "analyze_answer":
                    analyses = node_update.get("analyses") or []
                    if analyses:
                        latest_analysis = analyses[-1]
                        await _publish(interview_id, "analysis.completed", thread_id, {
                            "question_id": body.question_id,
                            "analysis": latest_analysis,
                        })
                elif node_name == "score_answer":
                    evaluations = node_update.get("evaluations") or []
                    if evaluations:
                        latest_eval = evaluations[-1]
                        await _publish(interview_id, "scoring.completed", thread_id, {
                            "question_id": body.question_id,
                            "evaluation": latest_eval,
                        })
                elif node_name == "update_evidence":
                    await _publish(interview_id, "evidence.updated", thread_id, {
                        "question_id": body.question_id,
                        "claim_statuses": node_update.get("claim_statuses", {}),
                    })
                elif node_name == "generate_coaching":
                    latest_coaching = node_update.get("latest_coaching")
                    if latest_coaching:
                        await _publish(interview_id, "coaching.ready", thread_id, {
                            "question_id": body.question_id,
                            "coaching": latest_coaching,
                        })
                elif node_name == "generate_question":
                    current_q = node_update.get("current_question")
                    if current_q:
                        await _publish(interview_id, "question.ready", thread_id, {
                            "question_id": current_q.get("question_id"),
                            "question_text": current_q.get("question_text"),
                            "turn_count": turn_count,
                        })
                elif node_name == "generate_report":
                    if node_update.get("finished"):
                        finished = True
                        final_report = node_update.get("final_report")
                        await _publish(interview_id, "interview.finished", thread_id, {
                            "stop_reason": node_update.get("stop_reason"),
                            "turn_count": turn_count,
                        })
                        if final_report:
                            await _publish(interview_id, "report.ready", thread_id, {})

        # Fetch the full final state for persistence
        snapshot = await interview_graph.aget_state(config)
        result_state = snapshot.values if snapshot else {}
        current_q = result_state.get("current_question") or current_q
        finished = result_state.get("finished", False) or finished
        turn_count = result_state.get("turn_count", 0) or turn_count
        latest_analysis = latest_analysis or (result_state.get("analyses") or [None])[-1]
        latest_eval = latest_eval or (result_state.get("evaluations") or [None])[-1]
        latest_coaching = latest_coaching or result_state.get("latest_coaching")
        final_report = final_report or result_state.get("final_report")

        if finished:
            interview.status = "finished"
            interview.finished_at = datetime.utcnow()

        # Save answer to DB
        latest_answer = result_state.get("answers", [])[-1] if result_state.get("answers") else {}
        db_answer = InterviewAnswer(
            answer_id=latest_answer.get("answer_id", new_answer_id()),
            interview_id=interview_id,
            question_id=body.question_id,
            answer_text=body.answer_text,
            analysis=latest_analysis,
            evaluation=latest_eval,
        )
        await session.merge(db_answer)

        # Save next question to DB (if any)
        if current_q and not finished:
            db_q = InterviewQuestion(
                question_id=current_q.get("question_id", new_question_id()),
                interview_id=interview_id,
                data=current_q,
            )
            await session.merge(db_q)

        # Save report if finished
        if finished and final_report:
            existing_report = await session.execute(
                select(InterviewReport).where(InterviewReport.interview_id == interview_id)
            )
            if not existing_report.scalar_one_or_none():
                db_report = InterviewReport(
                    report_id=new_id("rpt"),
                    interview_id=interview_id,
                    data=final_report,
                )
                session.add(db_report)

        await session.commit()

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("answer_submit_failed", error=str(e), traceback=traceback.format_exc(), interview_id=interview_id)
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {e}")

    return {
        "interview_id": interview_id,
        "status": "finished" if finished else "in_progress",
        "turn_count": turn_count,
        "current_question": current_q,
        "next_question": current_q.get("question_text") if current_q and not finished else None,
        "next_question_id": current_q.get("question_id") if current_q and not finished else None,
        "analysis": latest_analysis,
        "evaluation": latest_eval,
        "coaching": latest_coaching,
        "finished": finished,
    }


@router.post("/{interview_id}/finish")
async def finish_interview(
    interview_id: str,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Force finish an interview and generate report."""
    result = await session.execute(
        select(Interview).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user.user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "finished":
        return {"interview_id": interview_id, "status": "finished"}

    thread_id = interview.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # Drive graph to finish via Command update (not state mutation, which modifies a copy)
    try:
        result_state = await interview_graph.ainvoke(
            Command(
                resume={"answer_text": "[END OF INTERVIEW]"},
                update={"next_action": NextAction.FINISH.value, "stop_reason": "USER_REQUESTED"},
            ),
            config,
        )

        final_report = result_state.get("final_report")
    except Exception as e:
        logger.error("finish_failed", error=str(e), interview_id=interview_id)
        # Even if graph fails, mark as finished
        final_report = None

    interview.status = "finished"
    interview.finished_at = datetime.utcnow()

    # Save report
    if final_report:
        existing_report = await session.execute(
            select(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        if not existing_report.scalar_one_or_none():
            db_report = InterviewReport(
                report_id=new_id("rpt"),
                interview_id=interview_id,
                data=final_report,
            )
            session.add(db_report)

    await session.commit()

    # Publish SSE events
    turn_count = result_state.get("turn_count", 0) if result_state else 0
    await _publish(interview_id, "interview.finished", thread_id, {
        "stop_reason": "USER_REQUESTED",
        "turn_count": turn_count,
    })
    if final_report:
        await _publish(interview_id, "report.ready", thread_id, {})

    return {
        "interview_id": interview_id,
        "status": "finished",
        "has_report": final_report is not None,
    }
