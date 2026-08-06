"""Resume management API endpoints."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import PaginatedResponse
from app.core.deps import get_current_user
from app.core.enums import ResumeStatus
from app.core.ids import new_revision_id
from app.observability.logging import logger
from app.parsers.schemas import ResumeBlock as DocBlock
from app.parsers.schemas import ResumeDocument, SourceLocation
from app.persistence.database import get_session
from app.persistence.models import (
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    InterviewReport,
    ResumeBlock,
    ResumeRevision,
    ResumeSource,
    User,
)
from app.persistence.models import (
    ResumeClaim as DBClaim,
)
from app.persistence.models import (
    ResumeProfile as DBProfile,
)
from app.resume.claim_selection import select_core_claims
from app.resume.service import ResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


async def _resume_owned_by(
    session: AsyncSession, resume_id: str, user_id: str
) -> ResumeSource | None:
    """Fetch a resume only if it belongs to the given user (else None)."""
    result = await session.execute(
        select(ResumeSource).where(
            ResumeSource.resume_id == resume_id,
            ResumeSource.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


class TextUploadRequest(BaseModel):
    file_name: str
    text: str


class RevisionUpdateRequest(BaseModel):
    normalized_text: str


class ConfirmResponse(BaseModel):
    resume_id: str
    revision_id: str
    status: str
    message: str


class ClaimUpdateRequest(BaseModel):
    enabled: bool | None = None
    priority: int | None = None


async def _save_resume_to_db(
    session: AsyncSession,
    doc: ResumeDocument,
    content: bytes,
    user_id: str,
    revision_id: str | None = None,
    sha256: str | None = None,
) -> tuple[str, str]:
    """Save parsed resume document to database. Returns (resume_id, revision_id)."""
    if not revision_id:
        revision_id = new_revision_id()

    source = ResumeSource(
        resume_id=doc.resume_id,
        source_id=doc.source_id,
        user_id=user_id,
        file_name=doc.file_name,
        source_type=doc.source_type,
        sha256=sha256,
        file_size=len(content),
    )
    revision = ResumeRevision(
        revision_id=revision_id,
        resume_id=doc.resume_id,
        status=ResumeStatus.PARSED_UNCONFIRMED,
        raw_text=doc.raw_text,
        normalized_text=doc.normalized_text,
        extraction_method=doc.extraction_method,
        extraction_quality=doc.extraction_quality,
        extraction_warnings=doc.extraction_warnings,
        parser_name=doc.parser_name,
        parser_version=doc.parser_version,
    )

    await session.merge(source)
    await session.merge(revision)

    blocks = []
    for i, b in enumerate(doc.blocks):
        block = ResumeBlock(
            block_id=b.block_id,
            revision_id=revision_id,
            text=b.text,
            raw_text=b.raw_text,
            block_type=b.block_type,
            source_location=b.source_location.model_dump() if b.source_location else None,
            style_hints=dict(b.style_hints),
            warnings=list(b.warnings),
            block_index=i,
        )
        blocks.append(block)
    if blocks:
        session.add_all(blocks)

    await session.commit()
    return doc.resume_id, revision_id


@router.get("")
async def list_resumes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """List resumes with pagination, search, and filtering."""
    # Subquery: latest revision per resume
    latest_rev = (
        select(
            ResumeRevision.resume_id,
            ResumeRevision.revision_id,
            ResumeRevision.status,
            ResumeRevision.created_at,
            func.row_number()
            .over(
                partition_by=ResumeRevision.resume_id,
                order_by=ResumeRevision.created_at.desc(),
            )
            .label("rn"),
        )
    ).subquery()
    latest = select(
        latest_rev.c.resume_id,
        latest_rev.c.revision_id,
        latest_rev.c.status,
    ).where(latest_rev.c.rn == 1)
    latest_cte = latest.cte("latest_revision")

    base = (
        select(
            ResumeSource.resume_id,
            ResumeSource.file_name,
            ResumeSource.source_type,
            ResumeSource.created_at,
            latest_cte.c.status,
            latest_cte.c.revision_id,
        )
        .join(latest_cte, ResumeSource.resume_id == latest_cte.c.resume_id)
        .where(ResumeSource.user_id == user.user_id)
    )

    if search:
        base = base.where(ResumeSource.file_name.ilike(f"%{search}%"))
    if status:
        base = base.where(latest_cte.c.status == status)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_r = await session.execute(count_q)
    total = total_r.scalar() or 0

    # Sorting
    sort_col = ResumeSource.created_at if sort_by == "created_at" else ResumeSource.file_name
    if sort_order == "desc":
        base = base.order_by(sort_col.desc())
    else:
        base = base.order_by(sort_col.asc())

    # Pagination
    offset = (page - 1) * page_size
    base = base.offset(offset).limit(page_size)

    result = await session.execute(base)
    rows = result.all()

    items = [
        {
            "resume_id": row[0],
            "file_name": row[1],
            "source_type": row[2].value if hasattr(row[2], "value") else str(row[2]),
            "created_at": row[3].isoformat() if row[3] else None,
            "status": row[4].value if hasattr(row[4], "value") else str(row[4]) if row[4] else None,
            "latest_revision_id": row[5],
        }
        for row in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Upload a resume file (PDF, TXT, TEX)."""
    content = await file.read()
    mime = file.content_type
    sha256 = hashlib.sha256(content).hexdigest()

    service = ResumeService()
    doc = await service.parse_resume(content, file.filename or "resume", mime)

    revision_id = new_revision_id()
    await _save_resume_to_db(
        session, doc, content, user_id=user.user_id, revision_id=revision_id, sha256=sha256
    )

    logger.info("resume_uploaded", resume_id=doc.resume_id, quality=doc.extraction_quality)

    return {
        "resume_id": doc.resume_id,
        "revision_id": revision_id,
        "status": ResumeStatus.PARSED_UNCONFIRMED.value,
        "source_type": doc.source_type,
        "extraction_quality": doc.extraction_quality,
        "extraction_warnings": doc.extraction_warnings,
        "normalized_text": doc.normalized_text,
        "blocks": [b.model_dump() for b in doc.blocks],
    }


@router.post("/text")
async def upload_text(
    body: TextUploadRequest,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Upload resume as plain text."""
    content = body.text.encode("utf-8")
    sha256 = hashlib.sha256(content).hexdigest()
    service = ResumeService()
    doc = await service.parse_resume(content, body.file_name, "text/plain")

    revision_id = new_revision_id()
    await _save_resume_to_db(
        session, doc, content, user_id=user.user_id, revision_id=revision_id, sha256=sha256
    )

    logger.info("resume_text_uploaded", resume_id=doc.resume_id, quality=doc.extraction_quality)

    return {
        "resume_id": doc.resume_id,
        "revision_id": revision_id,
        "status": ResumeStatus.PARSED_UNCONFIRMED.value,
        "source_type": doc.source_type,
        "extraction_quality": doc.extraction_quality,
        "normalized_text": doc.normalized_text,
        "blocks": [b.model_dump() for b in doc.blocks],
    }


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get resume details."""
    result = await session.execute(
        select(ResumeSource).where(
            ResumeSource.resume_id == resume_id,
            ResumeSource.user_id == user.user_id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Get latest revision
    rev_result = await session.execute(
        select(ResumeRevision).where(
            ResumeRevision.resume_id == resume_id,
        ).order_by(ResumeRevision.created_at.desc()).limit(1)
    )
    rev = rev_result.scalar_one_or_none()

    # Get profile if exists
    profile_data = None
    if rev:
        profile_result = await session.execute(
            select(DBProfile).where(
                DBProfile.resume_id == resume_id,
                DBProfile.revision_id == rev.revision_id,
            )
        )
        profile_row = profile_result.scalar_one_or_none()
        if profile_row:
            profile_data = profile_row.data

    return {
        "resume_id": source.resume_id,
        "file_name": source.file_name,
        "source_type": source.source_type,
        "status": rev.status.value if rev else None,
        "revision_id": rev.revision_id if rev else None,
        "latest_revision_id": rev.revision_id if rev else None,
        "normalized_text": rev.normalized_text if rev else None,
        "raw_text": rev.raw_text if rev else None,
        "extraction_quality": rev.extraction_quality if rev else None,
        "extraction_warnings": rev.extraction_warnings if rev else [],
        "extraction_method": rev.extraction_method if rev else None,
        "parser_name": rev.parser_name if rev else None,
        "parser_version": rev.parser_version if rev else None,
        "profile": profile_data,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }


@router.get("/{resume_id}/claims")
async def get_claims(
    resume_id: str,
    revision_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get claims for a resume, optionally filtered by revision."""
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    query = select(DBClaim).where(DBClaim.resume_id == resume_id)
    if revision_id:
        query = query.where(DBClaim.claim_id.startswith(revision_id[:8]))

    result = await session.execute(query.order_by(DBClaim.priority.desc()))
    claims = result.scalars().all()
    profile_result = await session.execute(
        select(DBProfile)
        .where(DBProfile.resume_id == resume_id)
        .order_by(DBProfile.created_at.desc())
        .limit(1)
    )
    profile_row = profile_result.scalar_one_or_none()
    selected_data = select_core_claims(
        [claim.data for claim in claims],
        profile_row.data if profile_row else {},
    )
    selected_ids = {
        item.get("claim_id")
        for item in selected_data
    }
    claims = [
        claim
        for claim in claims
        if claim.data.get("claim_id") in selected_ids
    ]

    return {
        "resume_id": resume_id,
        "claims": [
            {
                "claim_id": c.claim_id,
                "priority": c.priority,
                "confidence": c.confidence,
                "disabled": c.disabled,
                "data": c.data,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in claims
        ],
    }


@router.patch("/{resume_id}/revisions/{revision_id}")
async def update_revision(
    resume_id: str,
    revision_id: str,
    body: RevisionUpdateRequest,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Update a parsed revision's normalized text and rebuild blocks."""
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    result = await session.execute(
        select(ResumeRevision).where(
            ResumeRevision.revision_id == revision_id,
            ResumeRevision.resume_id == resume_id,
        )
    )
    rev = result.scalar_one_or_none()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    if rev.status.value in ("CONFIRMED", "SUPERSEDED"):
        raise HTTPException(status_code=400, detail="Cannot update confirmed or superseded revision")

    rev.normalized_text = body.normalized_text

    # Rebuild blocks from updated normalized text
    # Re-parse using TextParser to get fresh blocks from the updated text
    from app.parsers.schemas import ParseInput
    from app.parsers.text_parser import TextParser

    text_parser = TextParser()
    parse_result = await text_parser.parse(ParseInput(
        source_id=resume_id,
        file_name="reparse.txt",
        content=body.normalized_text.encode("utf-8"),
    ))
    rev.extraction_quality = parse_result.extraction_quality
    rev.extraction_warnings = parse_result.extraction_warnings
    rev.extraction_method = parse_result.extraction_method
    rev.parser_name = parse_result.parser_name
    rev.parser_version = parse_result.parser_version

    # Replace old blocks with newly parsed ones
    # First delete existing blocks
    await session.execute(
        sa_delete(ResumeBlock).where(ResumeBlock.revision_id == revision_id)
    )

    # Add new blocks
    for i, b in enumerate(parse_result.blocks):
        block = ResumeBlock(
            block_id=b.block_id,
            revision_id=revision_id,
            text=b.text,
            raw_text=b.raw_text,
            block_type=b.block_type,
            source_location=b.source_location.model_dump() if b.source_location else None,
            style_hints=dict(b.style_hints),
            warnings=list(b.warnings),
            block_index=i,
        )
        session.add(block)

    await session.commit()

    return {
        "resume_id": resume_id,
        "revision_id": revision_id,
        "normalized_text": body.normalized_text,
        "extraction_quality": parse_result.extraction_quality,
        "extraction_warnings": parse_result.extraction_warnings,
    }


@router.post("/{resume_id}/revisions/{revision_id}/confirm")
async def confirm_revision(
    resume_id: str,
    revision_id: str,
    target_role: str = "",
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Confirm a parsed revision and generate profile + claims."""
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    result = await session.execute(
        select(ResumeRevision).options(
            selectinload(ResumeRevision.blocks),
            selectinload(ResumeRevision.source),
        ).where(
            ResumeRevision.revision_id == revision_id,
            ResumeRevision.resume_id == resume_id,
        )
    )
    rev = result.scalar_one_or_none()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    # Build ResumeDocument from revision data
    blocks = []
    for db_block in rev.blocks or []:
        blocks.append(DocBlock(
            block_id=db_block.block_id,
            text=db_block.text,
            raw_text=db_block.raw_text,
            block_type=db_block.block_type,
            source_location=SourceLocation(**db_block.source_location) if db_block.source_location else SourceLocation(),
        ))

    doc = ResumeDocument(
        resume_id=resume_id,
        source_id=resume_id,
        file_name="",
        source_type=rev.source.source_type if rev.source else "text",
        raw_text=rev.raw_text or "",
        normalized_text=rev.normalized_text or "",
        blocks=blocks,
        extraction_method=rev.extraction_method or "plain_text",
        extraction_quality=rev.extraction_quality or 0,
        parser_name=rev.parser_name or "",
        parser_version=rev.parser_version or "",
    )

    # Build profile
    service = ResumeService()
    profile = await service.build_profile(doc)

    # Never replace usable resume data with the deterministic empty fallback
    # when the upstream structured-generation call is temporarily unavailable.
    profile_build_failed = any(
        "Profile builder LLM call failed" in warning for warning in profile.warnings
    )
    if profile_build_failed:
        existing_result = await session.execute(
            select(DBProfile).where(DBProfile.resume_id == resume_id)
        )
        existing_profile = existing_result.scalar_one_or_none()
        existing_data = existing_profile.data if existing_profile else {}
        existing_entry_count = sum(
            len(existing_data.get(section, []))
            for section in ("education", "experiences", "projects", "research")
        )
        if existing_entry_count:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Resume parsing service is temporarily unavailable; "
                    "the existing parsed profile was preserved."
                ),
            )
        if not any(
            (profile.education, profile.experiences, profile.projects, profile.research)
        ):
            raise HTTPException(
                status_code=503,
                detail="Resume parsing service is temporarily unavailable; please retry.",
            )

    # Save profile
    db_profile = DBProfile(
        profile_id=profile.resume_id + "_profile",
        resume_id=resume_id,
        revision_id=revision_id,
        data=profile.model_dump(mode="json"),
        confidence=profile.extraction_confidence,
        warnings=profile.warnings,
    )
    await session.merge(db_profile)

    # Extract claims
    claims = await service.extract_claims(profile, target_role)
    # A rebuilt profile replaces, rather than appends to, its previous claims.
    await session.execute(
        sa_delete(DBClaim).where(DBClaim.resume_id == resume_id)
    )
    for claim in claims:
        db_claim = DBClaim(
            claim_id=claim.claim_id,
            resume_id=resume_id,
            data=claim.model_dump(mode="json"),
            priority=claim.priority,
            confidence=claim.confidence,
        )
        await session.merge(db_claim)

    # Update revision status
    rev.status = ResumeStatus.CONFIRMED
    await session.commit()

    logger.info("resume_confirmed", resume_id=resume_id, revision_id=revision_id, claims_count=len(claims))

    return {
        "resume_id": resume_id,
        "revision_id": revision_id,
        "status": ResumeStatus.CONFIRMED.value,
        "profile": profile.model_dump(mode="json"),
        "claims": [c.model_dump(mode="json") for c in claims],
    }


@router.patch("/{resume_id}/claims/{claim_id}")
async def update_claim(
    resume_id: str,
    claim_id: str,
    body: ClaimUpdateRequest,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Update a claim's enabled status or priority."""
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    result = await session.execute(
        select(DBClaim).where(
            DBClaim.claim_id == claim_id,
            DBClaim.resume_id == resume_id,
        )
    )
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if body.enabled is not None:
        claim.disabled = not body.enabled
    if body.priority is not None:
        if body.priority < 0 or body.priority > 100:
            raise HTTPException(status_code=400, detail="Priority must be 0-100")
        claim.priority = body.priority

    await session.commit()

    return {
        "claim_id": claim.claim_id,
        "resume_id": claim.resume_id,
        "priority": claim.priority,
        "disabled": claim.disabled,
    }


@router.get("/{resume_id}/revisions")
async def get_revisions(
    resume_id: str,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Get all revisions for a resume."""
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    result = await session.execute(
        select(ResumeRevision)
        .where(ResumeRevision.resume_id == resume_id)
        .order_by(ResumeRevision.created_at.desc())
    )
    revisions = result.scalars().all()

    if not revisions:
        # Check resume exists
        src_r = await session.execute(
            select(ResumeSource).where(ResumeSource.resume_id == resume_id)
        )
        if not src_r.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "resume_id": resume_id,
        "revisions": [
            {
                "revision_id": r.revision_id,
                "status": r.status.value,
                "extraction_quality": r.extraction_quality,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in revisions
        ],
    }


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    session: AsyncSession = Depends(get_session),
    user: Annotated[User, Depends(get_current_user)] = ...,
):
    """Delete a resume and all associated data (GDPR/right-to-delete).

    Covers: claims, profiles, blocks, revisions, source, interviews,
    interview questions, interview answers, interview reports.
    """
    if not await _resume_owned_by(session, resume_id, user.user_id):
        raise HTTPException(status_code=404, detail="Resume not found")

    # Get all interview IDs for this resume
    interview_ids_r = await session.execute(
        select(Interview.interview_id).where(Interview.resume_id == resume_id)
    )
    interview_ids = [row[0] for row in interview_ids_r.all()]

    # Delete interview-related data
    for iid in interview_ids:
        await session.execute(
            sa_delete(InterviewReport).where(InterviewReport.interview_id == iid)
        )
        await session.execute(
            sa_delete(InterviewAnswer).where(InterviewAnswer.interview_id == iid)
        )
        await session.execute(
            sa_delete(InterviewQuestion).where(InterviewQuestion.interview_id == iid)
        )
    if interview_ids:
        await session.execute(
            sa_delete(Interview).where(Interview.resume_id == resume_id)
        )

    # Delete resume-related data
    await session.execute(sa_delete(DBClaim).where(DBClaim.resume_id == resume_id))
    await session.execute(sa_delete(DBProfile).where(DBProfile.resume_id == resume_id))
    await session.execute(
        sa_delete(ResumeBlock).where(
            ResumeBlock.revision_id.in_(
                select(ResumeRevision.revision_id).where(ResumeRevision.resume_id == resume_id)
            )
        )
    )
    await session.execute(
        sa_delete(ResumeRevision).where(ResumeRevision.resume_id == resume_id)
    )
    await session.execute(
        sa_delete(ResumeSource).where(ResumeSource.resume_id == resume_id)
    )

    await session.commit()

    logger.info("resume_deleted", resume_id=resume_id)

    return {"resume_id": resume_id, "status": "deleted"}
