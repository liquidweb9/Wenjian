"""GDPR-compliant data deletion service.

M2.6: Handles cascade deletion of user data while preserving audit trail.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Dict, Any

from app.persistence.models import (
    User,
    ResumeSource,
    Interview,
    JobTarget,
    AbilityObservation,
    AbilityProfile,
    TrainingTask,
    LLMCall,
)


class DataDeletionService:
    """Service for GDPR-compliant data deletion."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_user_data(self, user_id: str, preserve_audit: bool = True) -> Dict[str, Any]:
        """Delete all user data with cascade.

        Args:
            user_id: User ID to delete
            preserve_audit: If True, preserve LLMCall audit records (anonymize user_id)

        Returns:
            Dict with deletion statistics

        Deletion order (respects foreign keys):
        1. TrainingTask (references user_id)
        2. AbilityProfile (references user_id)
        3. AbilityObservation (references user_id)
        4. Interviews + cascade (questions, answers, reports, contradictions, evidence, transitions, verification_points)
        5. Resumes + cascade (revisions, blocks, profiles, claims, mappings)
        6. JobTargets (references user_id)
        7. LLMCall (audit trail - anonymize if preserve_audit=True)
        8. User
        """
        stats = {
            "training_tasks": 0,
            "ability_profiles": 0,
            "ability_observations": 0,
            "interviews": 0,
            "resumes": 0,
            "job_targets": 0,
            "llm_calls_anonymized": 0,
            "llm_calls_deleted": 0,
            "user_deleted": False,
        }

        # Step 1: Delete TrainingTask records
        result = await self.session.execute(
            delete(TrainingTask).where(TrainingTask.user_id == user_id)
        )
        stats["training_tasks"] = result.rowcount

        # Step 2: Delete AbilityProfile records
        result = await self.session.execute(
            delete(AbilityProfile).where(AbilityProfile.user_id == user_id)
        )
        stats["ability_profiles"] = result.rowcount

        # Step 3: Delete AbilityObservation records
        result = await self.session.execute(
            delete(AbilityObservation).where(AbilityObservation.user_id == user_id)
        )
        stats["ability_observations"] = result.rowcount

        # Step 4: Get interview IDs then delete (cascade handled by DB)
        interview_stmt = select(Interview.interview_id).where(Interview.user_id == user_id)
        interview_result = await self.session.execute(interview_stmt)
        interview_ids = [row[0] for row in interview_result]

        if interview_ids:
            result = await self.session.execute(
                delete(Interview).where(Interview.user_id == user_id)
            )
            stats["interviews"] = result.rowcount

        # Step 5: Get resume IDs then delete (cascade handled by DB)
        resume_stmt = select(ResumeSource.resume_id).where(ResumeSource.user_id == user_id)
        resume_result = await self.session.execute(resume_stmt)
        resume_ids = [row[0] for row in resume_result]

        if resume_ids:
            result = await self.session.execute(
                delete(ResumeSource).where(ResumeSource.user_id == user_id)
            )
            stats["resumes"] = result.rowcount

        # Step 6: Delete JobTarget records (can be null user_id for templates)
        result = await self.session.execute(
            delete(JobTarget).where(JobTarget.user_id == user_id)
        )
        stats["job_targets"] = result.rowcount

        # Step 7: Handle LLMCall audit records
        if preserve_audit:
            # Anonymize: set user_id to NULL, keep call record
            llm_calls = await self.session.execute(
                select(LLMCall).where(LLMCall.interview_id.in_(interview_ids))
            )
            for call in llm_calls.scalars():
                call.interview_id = None  # Anonymize
                stats["llm_calls_anonymized"] += 1
        else:
            # Full deletion
            if interview_ids:
                result = await self.session.execute(
                    delete(LLMCall).where(LLMCall.interview_id.in_(interview_ids))
                )
                stats["llm_calls_deleted"] = result.rowcount

        # Step 8: Delete user record
        result = await self.session.execute(
            delete(User).where(User.user_id == user_id)
        )
        stats["user_deleted"] = result.rowcount == 1

        return stats

    async def delete_resume(self, resume_id: str, user_id: str) -> bool:
        """Delete a specific resume with cascade.

        Args:
            resume_id: Resume ID to delete
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found or unauthorized

        Cascade deletes:
        - ResumeRevision
        - ResumeBlock
        - ResumeProfile
        - ResumeClaim
        - ClaimCompetencyMapping
        - ClaimRequirementMapping
        """
        # Verify ownership
        stmt = select(ResumeSource).where(
            ResumeSource.resume_id == resume_id,
            ResumeSource.user_id == user_id
        )
        result = await self.session.execute(stmt)
        resume = result.scalar_one_or_none()

        if not resume:
            return False

        # Delete (cascade handled by DB foreign keys)
        await self.session.delete(resume)
        return True

    async def delete_interview(self, interview_id: str, user_id: str, preserve_audit: bool = True) -> bool:
        """Delete a specific interview with cascade.

        Args:
            interview_id: Interview ID to delete
            user_id: User ID (for ownership verification)
            preserve_audit: If True, anonymize LLMCall records

        Returns:
            True if deleted, False if not found or unauthorized

        Cascade deletes:
        - InterviewQuestion
        - InterviewAnswer
        - InterviewReport
        - VerificationPoint
        - Evidence
        - EvidenceTransition
        - Contradiction
        """
        # Verify ownership
        stmt = select(Interview).where(
            Interview.interview_id == interview_id,
            Interview.user_id == user_id
        )
        result = await self.session.execute(stmt)
        interview = result.scalar_one_or_none()

        if not interview:
            return False

        # Handle LLMCall audit records
        if preserve_audit:
            llm_calls = await self.session.execute(
                select(LLMCall).where(LLMCall.interview_id == interview_id)
            )
            for call in llm_calls.scalars():
                call.interview_id = None  # Anonymize
        else:
            await self.session.execute(
                delete(LLMCall).where(LLMCall.interview_id == interview_id)
            )

        # Delete interview (cascade handled by DB)
        await self.session.delete(interview)
        return True

    async def delete_job_target(self, job_target_id: str, user_id: str) -> bool:
        """Delete a specific job target.

        Args:
            job_target_id: JobTarget ID to delete
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found or unauthorized

        Note: Does not delete associated interviews (they remain with reference)
        """
        # Verify ownership
        stmt = select(JobTarget).where(
            JobTarget.job_target_id == job_target_id,
            JobTarget.user_id == user_id
        )
        result = await self.session.execute(stmt)
        job_target = result.scalar_one_or_none()

        if not job_target:
            return False

        await self.session.delete(job_target)
        return True
