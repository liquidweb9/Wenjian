"""Authentication endpoints: register, login, get current user.

M2.6: Real authentication with JWT tokens.
"""

from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.core.ids import new_id
from app.core.data_deletion import DataDeletionService
from app.persistence.database import get_session
from app.persistence.repositories import UserRepository
from app.persistence.models import User

router = APIRouter(tags=["auth"])


# ============================================================
# Request/Response Models
# ============================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None


class DeletionStatsResponse(BaseModel):
    """Response model for data deletion statistics."""
    training_tasks: int
    ability_profiles: int
    ability_observations: int
    interviews: int
    resumes: int
    job_targets: int
    llm_calls_anonymized: int
    llm_calls_deleted: int
    user_deleted: bool
    message: str


# ============================================================
# Endpoints
# ============================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Register a new user account.

    Creates user with hashed password and returns JWT token.

    Raises:
        400: Email already registered
    """
    user_repo = UserRepository(session)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        user_id=new_id("user"),
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        is_active=True,
        is_verified=False,
    )

    await user_repo.create(user)
    await session.commit()

    # Generate access token
    access_token = create_access_token(data={"sub": user.user_id})

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Login with email and password.

    Returns JWT token on success.

    Raises:
        401: Invalid credentials or inactive account
    """
    user_repo = UserRepository(session)

    # Get user by email
    user = await user_repo.get_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Update last login
    await user_repo.update_last_login(user.user_id)
    await session.commit()

    # Generate access token
    access_token = create_access_token(data={"sub": user.user_id})

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: Annotated[User, Depends(get_current_user)],
):
    """Get current user profile.

    Requires valid JWT token in Authorization header.

    Returns:
        Current user's profile information
    """
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


# ============================================================
# GDPR Data Deletion Endpoints (M2.6)
# ============================================================

@router.delete("/me", response_model=DeletionStatsResponse)
async def delete_my_account(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    preserve_audit: bool = True,
):
    """Delete current user's account and all associated data (GDPR compliance).

    This performs cascade deletion of:
    - All resumes and associated data (revisions, blocks, profiles, claims, mappings)
    - All interviews and associated data (questions, answers, reports, evidence, contradictions)
    - All job targets created by user
    - All ability profiles and observations
    - All training tasks
    - User account

    Args:
        preserve_audit: If True (default), anonymize LLMCall audit records instead of deleting

    Raises:
        500: Deletion failed
    """
    deletion_service = DataDeletionService(session)

    try:
        stats = await deletion_service.delete_user_data(
            user_id=user.user_id,
            preserve_audit=preserve_audit
        )
        await session.commit()

        return DeletionStatsResponse(
            **stats,
            message=f"Account {user.email} and all associated data deleted successfully"
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a specific resume and all associated data.

    Cascade deletes:
    - Resume revisions
    - Resume blocks
    - Resume profiles
    - Resume claims
    - Claim mappings

    Raises:
        404: Resume not found or unauthorized
    """
    deletion_service = DataDeletionService(session)

    deleted = await deletion_service.delete_resume(resume_id, user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or you don't have permission to delete it"
        )

    await session.commit()


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    preserve_audit: bool = True,
):
    """Delete a specific interview and all associated data.

    Cascade deletes:
    - Interview questions
    - Interview answers
    - Interview report
    - Verification points
    - Evidence records
    - Evidence transitions
    - Contradictions

    Args:
        preserve_audit: If True (default), anonymize LLMCall audit records

    Raises:
        404: Interview not found or unauthorized
    """
    deletion_service = DataDeletionService(session)

    deleted = await deletion_service.delete_interview(interview_id, user.user_id, preserve_audit)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or you don't have permission to delete it"
        )

    await session.commit()


@router.delete("/job-targets/{job_target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_target(
    job_target_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a specific job target.

    Note: Associated interviews are not deleted (they remain with reference).

    Raises:
        404: Job target not found or unauthorized
    """
    deletion_service = DataDeletionService(session)

    deleted = await deletion_service.delete_job_target(job_target_id, user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job target not found or you don't have permission to delete it"
        )

    await session.commit()
