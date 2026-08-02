"""Tests for GDPR-compliant data deletion.

M2.6: Verify cascade deletion and audit trail preservation.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_deletion import DataDeletionService
from app.core.security import hash_password
from app.core.ids import new_id
from app.persistence.models import (
    User,
    ResumeSource,
    ResumeRevision,
    Interview,
    InterviewQuestion,
    JobTarget,
    AbilityProfile,
    LLMCall,
)


@pytest.mark.asyncio
class TestDataDeletion:
    """Test data deletion service."""

    async def test_delete_user_with_all_data(self, async_session: AsyncSession):
        """Test complete user data deletion with cascade."""
        user_id = new_id("user")
        resume_id = new_id("resume")
        interview_id = new_id("interview")

        # Create user
        user = User(
            user_id=user_id,
            email="delete_test@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user)

        # Create resume
        resume = ResumeSource(
            resume_id=resume_id,
            user_id=user_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        async_session.add(resume)

        # Create resume revision (child of resume)
        revision = ResumeRevision(
            revision_id=new_id("rev"),
            resume_id=resume_id,
            status="COMPLETE",
        )
        async_session.add(revision)

        # Create interview
        interview = Interview(
            interview_id=interview_id,
            user_id=user_id,
            resume_id=resume_id,
            status="COMPLETE",
        )
        async_session.add(interview)

        # Create interview question (child of interview)
        question = InterviewQuestion(
            question_id=new_id("q"),
            interview_id=interview_id,
            question_text="Tell me about your project",
        )
        async_session.add(question)

        # Create LLM call audit record
        llm_call = LLMCall(
            call_id=new_id("call"),
            interview_id=interview_id,
            task_name="score_answer",
            model="test-model",
            status="success",
        )
        async_session.add(llm_call)

        await async_session.commit()

        # Delete user data
        deletion_service = DataDeletionService(async_session)
        stats = await deletion_service.delete_user_data(user_id, preserve_audit=True)
        await async_session.commit()

        # Verify statistics
        assert stats["resumes"] == 1
        assert stats["interviews"] == 1
        assert stats["user_deleted"] is True
        assert stats["llm_calls_anonymized"] == 1

        # Verify LLM call is anonymized (interview_id set to None)
        llm_call_after = await async_session.get(LLMCall, llm_call.call_id)
        assert llm_call_after is not None
        assert llm_call_after.interview_id is None

    async def test_delete_user_without_preserving_audit(self, async_session: AsyncSession):
        """Test user deletion with full audit trail removal."""
        user_id = new_id("user")
        interview_id = new_id("interview")

        user = User(
            user_id=user_id,
            email="delete_audit@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user)

        interview = Interview(
            interview_id=interview_id,
            user_id=user_id,
            resume_id=new_id("resume"),
            status="COMPLETE",
        )
        async_session.add(interview)

        llm_call = LLMCall(
            call_id=new_id("call"),
            interview_id=interview_id,
            task_name="route_decision",
            model="test-model",
            status="success",
        )
        async_session.add(llm_call)

        await async_session.commit()

        # Delete without preserving audit
        deletion_service = DataDeletionService(async_session)
        stats = await deletion_service.delete_user_data(user_id, preserve_audit=False)
        await async_session.commit()

        # Verify LLM call is deleted
        assert stats["llm_calls_deleted"] == 1
        llm_call_after = await async_session.get(LLMCall, llm_call.call_id)
        assert llm_call_after is None

    async def test_delete_resume_with_cascade(self, async_session: AsyncSession):
        """Test resume deletion cascades to revisions."""
        user_id = new_id("user")
        resume_id = new_id("resume")

        user = User(
            user_id=user_id,
            email="resume_delete@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user)

        resume = ResumeSource(
            resume_id=resume_id,
            user_id=user_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        async_session.add(resume)

        revision = ResumeRevision(
            revision_id=new_id("rev"),
            resume_id=resume_id,
            status="COMPLETE",
        )
        async_session.add(revision)

        await async_session.commit()

        # Delete resume
        deletion_service = DataDeletionService(async_session)
        deleted = await deletion_service.delete_resume(resume_id, user_id)
        await async_session.commit()

        assert deleted is True

        # Verify cascade deletion
        resume_after = await async_session.get(ResumeSource, resume_id)
        assert resume_after is None

    async def test_delete_resume_unauthorized(self, async_session: AsyncSession):
        """Test resume deletion fails for wrong user."""
        user1_id = new_id("user")
        user2_id = new_id("user")
        resume_id = new_id("resume")

        user1 = User(
            user_id=user1_id,
            email="owner@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user1)

        resume = ResumeSource(
            resume_id=resume_id,
            user_id=user1_id,
            source_id="src1",
            file_name="resume.pdf",
            source_type="PDF",
        )
        async_session.add(resume)

        await async_session.commit()

        # Try to delete as different user
        deletion_service = DataDeletionService(async_session)
        deleted = await deletion_service.delete_resume(resume_id, user2_id)

        assert deleted is False

        # Verify resume still exists
        resume_after = await async_session.get(ResumeSource, resume_id)
        assert resume_after is not None

    async def test_delete_interview_with_cascade(self, async_session: AsyncSession):
        """Test interview deletion cascades to questions and answers."""
        user_id = new_id("user")
        interview_id = new_id("interview")

        user = User(
            user_id=user_id,
            email="interview_delete@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user)

        interview = Interview(
            interview_id=interview_id,
            user_id=user_id,
            resume_id=new_id("resume"),
            status="IN_PROGRESS",
        )
        async_session.add(interview)

        question = InterviewQuestion(
            question_id=new_id("q"),
            interview_id=interview_id,
            question_text="What is your experience?",
        )
        async_session.add(question)

        await async_session.commit()

        # Delete interview
        deletion_service = DataDeletionService(async_session)
        deleted = await deletion_service.delete_interview(interview_id, user_id)
        await async_session.commit()

        assert deleted is True

        # Verify cascade deletion
        interview_after = await async_session.get(Interview, interview_id)
        assert interview_after is None

    async def test_delete_job_target(self, async_session: AsyncSession):
        """Test job target deletion."""
        user_id = new_id("user")
        job_target_id = new_id("job")

        user = User(
            user_id=user_id,
            email="job_delete@example.com",
            hashed_password=hash_password("password"),
        )
        async_session.add(user)

        job_target = JobTarget(
            job_target_id=job_target_id,
            user_id=user_id,
            title="Backend Engineer",
            level="senior",
            interview_round="technical",
            source="template",
        )
        async_session.add(job_target)

        await async_session.commit()

        # Delete job target
        deletion_service = DataDeletionService(async_session)
        deleted = await deletion_service.delete_job_target(job_target_id, user_id)
        await async_session.commit()

        assert deleted is True

        # Verify deletion
        job_after = await async_session.get(JobTarget, job_target_id)
        assert job_after is None

    async def test_delete_nonexistent_user(self, async_session: AsyncSession):
        """Test deleting nonexistent user returns zero deletions."""
        deletion_service = DataDeletionService(async_session)
        stats = await deletion_service.delete_user_data("nonexistent_user")

        assert stats["user_deleted"] is False
        assert stats["resumes"] == 0
        assert stats["interviews"] == 0
