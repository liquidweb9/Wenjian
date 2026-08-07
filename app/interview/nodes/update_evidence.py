"""Update evidence ledger and claim statuses based on latest evaluation.

Phase 2: Integrates Evidence Engine 2.0 with state machine, span extraction,
and contradiction detection.
"""

from app.core.enums import ClaimStatusEnum
from app.core.ids import new_id

# Phase 2 imports
from app.evidence import (
    ContradictionDetector,
    EvidenceSpanExtractor,
    EvidenceState,
    EvidenceStateMachine,
    ReasonCode,
    TransitionContext,
)
from app.interview.schemas import EvidenceItem
from app.interview.state import InterviewState
from app.llm.agnes_api import AgnesGateway
from app.observability.logging import logger
from app.persistence.database import async_session_factory
from app.persistence.models import (
    Contradiction,
    Evidence,
    EvidenceTransition,
    VerificationPoint,
)
from app.persistence.repositories.evidence_repo import EvidenceRepository


def _count_vpoints(state: InterviewState, claim_id: str) -> int:
    """Count total verification points for a claim."""
    for rc in state.get("resume_claims", []):
        if rc.get("claim_id") == claim_id:
            return len(rc.get("verification_points", []))
    return 1


def _get_vp_from_claim(state: InterviewState, claim_id: str, vp_id: str) -> dict | None:
    """Get verification point dict from claim.

    Claim verification points use ``point_id`` as their identifier; questions
    reference the same value as ``verification_point_id``.
    """
    for rc in state.get("resume_claims", []):
        if rc.get("claim_id") == claim_id:
            for vp in rc.get("verification_points", []):
                if (vp.get("verification_point_id") or vp.get("point_id")) == vp_id:
                    return vp
    return None


async def update_evidence_node(state: InterviewState) -> dict:
    """Update claim statuses and evidence based on latest analysis/evaluation.

    Phase 2: Uses Evidence Engine 2.0 components:
    - EvidenceStateMachine for state transitions
    - EvidenceSpanExtractor for extracting evidence from answers
    - ContradictionDetector for detecting contradictions
    - Persists to database tables (VerificationPoint, Evidence, EvidenceTransition, Contradiction)
    """
    claim_statuses = dict(state.get("claim_statuses", {}))
    evaluations = state.get("evaluations", [])
    analyses = state.get("analyses", [])
    answers = state.get("answers", [])
    questions = state.get("questions", [])
    evidence_items = list(state.get("evidence_items", []))
    contradictions_list = list(state.get("contradictions", []))
    current_claim_id = state.get("current_claim_id")
    current_vp_id = state.get("current_verification_point_id")
    interview_id = state.get("interview_id")

    if not evaluations or not current_claim_id:
        return {}

    latest_eval = evaluations[-1]
    latest_analysis = analyses[-1] if analyses else {}
    latest_answer = answers[-1] if answers else {}
    latest_question = questions[-1] if questions else {}

    # Initialize Evidence Engine 2.0 components
    llm = AgnesGateway()
    interview_tier = state.get("model_tier")
    state_machine = EvidenceStateMachine()
    span_extractor = EvidenceSpanExtractor(llm=llm, model_tier=interview_tier)
    contradiction_detector = ContradictionDetector(llm=llm, id_generator=lambda: new_id("ct"), model_tier=interview_tier)

    # Create database session
    async with async_session_factory() as session:
        try:
            evidence_repo = EvidenceRepository(session)

            # ============================================================
            # Phase 2: Evidence Engine Integration
            # ============================================================

            if current_vp_id:
                # Get or create verification point
                vp_record = await evidence_repo.get_verification_point(current_vp_id)

                if not vp_record:
                    # Create new verification point record
                    vp_dict = _get_vp_from_claim(state, current_claim_id, current_vp_id)
                    if vp_dict:
                        vp_record = VerificationPoint(
                            verification_point_id=current_vp_id,
                            claim_id=current_claim_id,
                            competency_code=vp_dict.get("competency_code", ""),
                            requirement_id=vp_dict.get("requirement_id"),
                            aspect=vp_dict.get("aspect") or vp_dict.get("description") or "",
                            expected_evidence=vp_dict.get("expected_evidence", {}),
                            current_state=EvidenceState.UNSEEN.value,
                            strength=None,
                            confidence=None,
                            unresolved_reason_codes=None,
                        )
                        await evidence_repo.add_verification_point(vp_record)
                        await session.commit()
                        await session.refresh(vp_record)

                # Extract evidence spans from answer
                answer_text = latest_answer.get("answer_text", "")
                answer_id = latest_answer.get("answer_id", "")

                vp_for_extraction = {
                    "verification_point_id": current_vp_id,
                    "aspect": vp_record.aspect if vp_record else "",
                    "expected_evidence": vp_record.expected_evidence if vp_record else {},
                }

                span_result = await span_extractor.extract_spans(
                    answer_text=answer_text,
                    answer_id=answer_id,
                    verification_point=vp_for_extraction,
                )

                # Save evidence spans to database
                for span in span_result.spans:
                    evidence_record = Evidence(
                        evidence_id=new_id("ev"),
                        verification_point_id=current_vp_id,
                        interview_id=interview_id,
                        answer_id=answer_id,
                        evidence_type=span.evidence_type,
                        spans=[{
                            "start": span.start,
                            "end": span.end,
                            "text": span.text,
                            "quote_hash": span.quote_hash,
                        }],
                        summary=span_result.summary,
                        extracted_by="MODEL",
                        confidence=span_result.confidence,
                    )
                    await evidence_repo.add_evidence(evidence_record)

                # Get all answers for this verification point (for contradiction detection)
                related_answers = []
                for ans in answers:
                    # Check if answer relates to this verification point
                    ans_vp_id = None
                    for q in questions:
                        if q.get("question_id") == ans.get("question_id"):
                            ans_vp_id = q.get("verification_point_id")
                            break

                    if ans_vp_id == current_vp_id:
                        related_answers.append({
                            "answer_id": ans.get("answer_id", ""),
                            "question_text": next(
                                (q.get("question_text", "") for q in questions
                                 if q.get("question_id") == ans.get("question_id")),
                                ""
                            ),
                            "answer_text": ans.get("answer_text", ""),
                        })

                # Detect contradictions
                contradiction_result = await contradiction_detector.detect_contradictions(
                    verification_point=vp_for_extraction,
                    answers=related_answers,
                )

                # Save contradictions to database
                for contradiction in contradiction_result.contradictions:
                    contradiction_record = Contradiction(
                        contradiction_id=contradiction.contradiction_id,
                        verification_point_id=current_vp_id,
                        interview_id=interview_id,
                        claim_id=current_claim_id,
                        conflicting_answers=contradiction.conflicting_answers,
                        contradiction_type=contradiction.contradiction_type,
                        severity=contradiction.severity,
                        description=contradiction.description,
                        clarification_question=contradiction.clarification_question,
                        resolution_status="UNRESOLVED",
                        resolution_answer_id=None,
                        resolved_at=None,
                    )
                    await evidence_repo.add_contradiction(contradiction_record)

                    # Add to state contradictions list
                    contradictions_list.append({
                        "contradiction_id": contradiction.contradiction_id,
                        "verification_point_id": current_vp_id,
                        "claim_id": current_claim_id,
                        "type": contradiction.contradiction_type,
                        "severity": contradiction.severity,
                        "description": contradiction.description,
                    })

                # Prepare transition context
                missing = latest_analysis.get("missing_expected_points", [])
                addressed = latest_analysis.get("addressed_expected_points", [])
                has_contradictions = len(contradiction_result.contradictions) > 0

                context = TransitionContext(
                    verification_point_id=current_vp_id,
                    interview_id=interview_id,
                    answer_id=answer_id,
                    has_evidence_spans=(len(span_result.spans) > 0),
                    strength=span_result.confidence,
                    confidence="HIGH" if span_result.confidence >= 0.8 else "MEDIUM" if span_result.confidence >= 0.5 else "LOW",
                    has_contradiction=has_contradictions,
                    contradiction_details={"description": contradiction_result.contradictions[0].description, "severity": contradiction_result.contradictions[0].severity} if has_contradictions else None,
                )

                # Determine reason code
                if has_contradictions:
                    reason_code = ReasonCode.CONTRADICTION_DETECTED
                elif not addressed and not missing:
                    reason_code = ReasonCode.NO_EVIDENCE
                elif addressed and not missing:
                    reason_code = ReasonCode.EVIDENCE_SPANS_FOUND
                elif addressed and missing:
                    reason_code = ReasonCode.HAS_ANSWER
                else:
                    reason_code = ReasonCode.NO_EVIDENCE

                # Determine target state based on evidence and contradictions
                current_state = EvidenceState(vp_record.current_state) if vp_record else EvidenceState.UNSEEN

                # Determine target state
                if has_contradictions:
                    target_state = EvidenceState.CONTRADICTORY
                elif len(span_result.spans) > 0 and span_result.confidence >= 0.7 and not missing:
                    target_state = EvidenceState.VERIFIED
                elif len(span_result.spans) > 0:
                    target_state = EvidenceState.PARTIALLY_SUPPORTED
                elif addressed:
                    target_state = EvidenceState.ADDRESSED
                else:
                    target_state = current_state  # No transition

                # Attempt state transition
                success, transition_reason, msg = state_machine.can_transition(
                    current_state=current_state,
                    target_state=target_state,
                    context=context,
                )

                if success and vp_record and target_state != current_state:
                    # Record transition
                    transition_record = EvidenceTransition(
                        transition_id=new_id("tr"),
                        verification_point_id=current_vp_id,
                        interview_id=interview_id,
                        from_state=current_state.value,
                        to_state=target_state.value,
                        reason_code=transition_reason.value if transition_reason else reason_code.value,
                        answer_id=answer_id,
                        evaluation_id=latest_eval.get("evaluation_id"),
                        evidence_spans=[
                            {
                                "start": span.start,
                                "end": span.end,
                                "text": span.text,
                                "quote_hash": span.quote_hash,
                            }
                            for span in span_result.spans
                        ] if span_result.spans else None,
                        policy_version="1.0",
                        prompt_version=None,
                        model_name=None,
                    )
                    await evidence_repo.add_transition(transition_record)

                    # Update verification point state
                    await evidence_repo.update_verification_point_state(
                        verification_point_id=current_vp_id,
                        new_state=target_state.value,
                        strength=span_result.confidence if span_result.spans else None,
                        confidence=context.confidence if span_result.spans else None,
                        unresolved_reason_codes=[reason_code.value] if target_state != EvidenceState.VERIFIED else None,
                    )

                    logger.info("evidence_state_transition",
                                vp_id=current_vp_id,
                                from_state=current_state.value,
                                to_state=target_state.value,
                                reason_code=transition_reason.value if transition_reason else reason_code.value,
                                has_spans=len(span_result.spans) > 0,
                                has_contradictions=has_contradictions)

            # ============================================================
            # Phase 1 Compatibility: Update claim statuses
            # ============================================================

            # Create evidence item (Phase 1 format)
            if latest_answer and latest_analysis:
                evidence = EvidenceItem(
                    evidence_id=new_id("ev"),
                    claim_id=current_claim_id,
                    verification_point_id=current_vp_id,
                    question_id=latest_question.get("question_id", ""),
                    answer_id=latest_answer.get("answer_id", ""),
                    evidence_text=latest_answer.get("answer_text", "")[:500],
                    evidence_type="technical",
                    strength=latest_eval.get("evaluation_confidence", 0.5) if latest_eval else 0.5,
                    confidence=latest_eval.get("evaluation_confidence", 0.5) if latest_eval else 0.5,
                )
                evidence_items.append(evidence.model_dump(mode="json"))

            # Update claim status (Phase 1 logic)
            if current_claim_id in claim_statuses:
                status = claim_statuses[current_claim_id]

                if current_vp_id:
                    missing = latest_analysis.get("missing_expected_points", [])
                    addressed = latest_analysis.get("addressed_expected_points", [])

                    if not missing and addressed:
                        if current_vp_id not in status["verified_points"]:
                            status["verified_points"].append(current_vp_id)
                    elif addressed:
                        if current_vp_id not in status["partial_points"]:
                            status["partial_points"].append(current_vp_id)
                    else:
                        if current_vp_id not in status["missing_points"]:
                            status["missing_points"].append(current_vp_id)

                # Update overall status
                verified_count = len(status["verified_points"])
                total_vpoints = _count_vpoints(state, current_claim_id)
                contradictions = latest_analysis.get("possible_contradictions", [])

                if contradictions or len(contradictions_list) > 0:
                    status["status"] = ClaimStatusEnum.CONTRADICTORY.value
                elif verified_count >= total_vpoints and total_vpoints > 0:
                    status["status"] = ClaimStatusEnum.VERIFIED.value
                elif verified_count > 0:
                    status["status"] = ClaimStatusEnum.PARTIALLY_VERIFIED.value
                else:
                    status["status"] = ClaimStatusEnum.IN_PROGRESS.value

                status["confidence"] = max(0.1, min(1.0, verified_count / max(total_vpoints, 1)))
                claim_statuses[current_claim_id] = status

            # Update coverage (Phase 1 logic)
            coverage = dict(state.get("coverage", {}))
            plan = state.get("interview_plan", {})
            for topic in plan.get("topics", []):
                related = topic.get("related_claim_ids", [])
                if current_claim_id in related:
                    tid = topic.get("topic_id", "")
                    covered = sum(
                        1 for cid in related
                        if claim_statuses.get(cid, {}).get("status") in (
                            ClaimStatusEnum.VERIFIED.value,
                            ClaimStatusEnum.PARTIALLY_VERIFIED.value,
                        )
                    )
                    coverage[tid] = covered / max(len(related), 1)

            # Commit all database changes
            await session.commit()

            logger.info("evidence_updated",
                        claim_id=current_claim_id,
                        status=claim_statuses.get(current_claim_id, {}).get("status"),
                        evidence_count=len(evidence_items),
                        phase2_enabled=True)

            return {
                "claim_statuses": claim_statuses,
                "coverage": coverage,
                "evidence_items": evidence_items,
                "contradictions": contradictions_list,
            }

        except Exception as e:
            await session.rollback()
            logger.error("evidence_update_failed", error=str(e), claim_id=current_claim_id)

            # Fallback to Phase 1 behavior on error
            return {
                "claim_statuses": claim_statuses,
                "coverage": dict(state.get("coverage", {})),
                "evidence_items": evidence_items,
            }
