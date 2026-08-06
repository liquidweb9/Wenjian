"""GDPR-compliant data deletion service.

M2.6: Handles cascade deletion of user data while preserving audit trail.
"""

from typing import Any, Dict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import (
    AbilityObservation,
    AbilityProfile,
    ClaimCompetencyMapping,
    ClaimRequirementMapping,
    Contradiction,
    Evidence,
    EvidenceTransition,
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    InterviewReport,
    JobTarget,
    LLMCall,
    ResumeBlock,
    ResumeClaim,
    ResumeProfile,
    ResumeRevision,
    ResumeSource,
    TrainingTask,
    User,
    VerificationPoint,
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

        Deletion order (children before parents so foreign keys hold on
        PostgreSQL, where FK constraints are enforced):
        1. TrainingTask / AbilityProfile / AbilityObservation (reference user_id)
        2. LLMCall audit (anonymize or delete by interview_id, before interviews go)
        3. Interview children -> Interviews
        4. Claim mappings / verification points -> ResumeClaims / Profiles / Blocks / Revisions -> ResumeSources
        5. JobTargets
        6. User
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

        # Step 1: User-scoped child tables
        result = await self.session.execute(
            delete(TrainingTask).where(TrainingTask.user_id == user_id)
        )
        stats["training_tasks"] = result.rowcount

        result = await self.session.execute(
            delete(AbilityProfile).where(AbilityProfile.user_id == user_id)
        )
        stats["ability_profiles"] = result.rowcount

        result = await self.session.execute(
            delete(AbilityObservation).where(AbilityObservation.user_id == user_id)
        )
        stats["ability_observations"] = result.rowcount

        # Step 2: Collect interview IDs, then handle LLMCall audit before deleting interviews
        interview_result = await self.session.execute(
            select(Interview.interview_id).where(Interview.user_id == user_id)
        )
        interview_ids = [row[0] for row in interview_result]

        if interview_ids:
            if preserve_audit:
                llm_calls = await self.session.execute(
                    select(LLMCall).where(LLMCall.interview_id.in_(interview_ids))
                )
                for call in llm_calls.scalars():
                    call.interview_id = None  # Anonymize
                    stats["llm_calls_anonymized"] += 1
            else:
                result = await self.session.execute(
                    delete(LLMCall).where(LLMCall.interview_id.in_(interview_ids))
                )
                stats["llm_calls_deleted"] = result.rowcount

        # Step 3: Interview children, then interviews
        if interview_ids:
            await self.session.execute(
                delete(EvidenceTransition).where(EvidenceTransition.interview_id.in_(interview_ids))
            )
            await self.session.execute(
                delete(Evidence).where(Evidence.interview_id.in_(interview_ids))
            )
            await self.session.execute(
                delete(Contradiction).where(Contradiction.interview_id.in_(interview_ids))
            )
            await self.session.execute(
                delete(InterviewReport).where(InterviewReport.interview_id.in_(interview_ids))
            )
            await self.session.execute(
                delete(InterviewAnswer).where(InterviewAnswer.interview_id.in_(interview_ids))
            )
            await self.session.execute(
                delete(InterviewQuestion).where(InterviewQuestion.interview_id.in_(interview_ids))
            )
            result = await self.session.execute(
                delete(Interview).where(Interview.user_id == user_id)
            )
            stats["interviews"] = result.rowcount

        # Step 4: Resume children, then resumes
        resume_result = await self.session.execute(
            select(ResumeSource.resume_id).where(ResumeSource.user_id == user_id)
        )
        resume_ids = [row[0] for row in resume_result]

        if resume_ids:
            claim_result = await self.session.execute(
                select(ResumeClaim.claim_id).where(ResumeClaim.resume_id.in_(resume_ids))
            )
            claim_ids = [row[0] for row in claim_result]
            if claim_ids:
                await self.session.execute(
                    delete(ClaimCompetencyMapping).where(ClaimCompetencyMapping.claim_id.in_(claim_ids))
                )
                await self.session.execute(
                    delete(ClaimRequirementMapping).where(ClaimRequirementMapping.claim_id.in_(claim_ids))
                )
                # Verification points reference claim_id (and requirement_id); evidence/
                # transitions/contradictions referencing them are already gone in step 3.
                await self.session.execute(
                    delete(VerificationPoint).where(VerificationPoint.claim_id.in_(claim_ids))
                )
            await self.session.execute(
                delete(ResumeClaim).where(ResumeClaim.resume_id.in_(resume_ids))
            )
            await self.session.execute(
                delete(ResumeProfile).where(ResumeProfile.resume_id.in_(resume_ids))
            )
            revision_result = await self.session.execute(
                select(ResumeRevision.revision_id).where(ResumeRevision.resume_id.in_(resume_ids))
            )
            revision_ids = [row[0] for row in revision_result]
            if revision_ids:
                await self.session.execute(
                    delete(ResumeBlock).where(ResumeBlock.revision_id.in_(revision_ids))
                )
                await self.session.execute(
                    delete(ResumeRevision).where(ResumeRevision.resume_id.in_(resume_ids))
                )
            result = await self.session.execute(
                delete(ResumeSource).where(ResumeSource.user_id == user_id)
            )
            stats["resumes"] = result.rowcount

        # Step 5: JobTarget records (can be null user_id for templates)
        result = await self.session.execute(
            delete(JobTarget).where(JobTarget.user_id == user_id)
        )
        stats["job_targets"] = result.rowcount

        # Step 6: Delete user record
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

        Cascade deletes (children first for PostgreSQL FK enforcement):
        - Claim mappings, verification points, claims, profiles
        - Blocks and revisions
        - The resume source
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

        claim_result = await self.session.execute(
            select(ResumeClaim.claim_id).where(ResumeClaim.resume_id == resume_id)
        )
        claim_ids = [row[0] for row in claim_result]
        if claim_ids:
            await self.session.execute(
                delete(ClaimCompetencyMapping).where(ClaimCompetencyMapping.claim_id.in_(claim_ids))
            )
            await self.session.execute(
                delete(ClaimRequirementMapping).where(ClaimRequirementMapping.claim_id.in_(claim_ids))
            )
            await self.session.execute(
                delete(VerificationPoint).where(VerificationPoint.claim_id.in_(claim_ids))
            )
        await self.session.execute(delete(ResumeClaim).where(ResumeClaim.resume_id == resume_id))
        await self.session.execute(delete(ResumeProfile).where(ResumeProfile.resume_id == resume_id))

        revision_result = await self.session.execute(
            select(ResumeRevision.revision_id).where(ResumeRevision.resume_id == resume_id)
        )
        revision_ids = [row[0] for row in revision_result]
        if revision_ids:
            await self.session.execute(
                delete(ResumeBlock).where(ResumeBlock.revision_id.in_(revision_ids))
            )
            await self.session.execute(
                delete(ResumeRevision).where(ResumeRevision.resume_id == resume_id)
            )

        await self.session.execute(delete(ResumeSource).where(ResumeSource.resume_id == resume_id))
        return True

    async def delete_interview(self, interview_id: str, user_id: str, preserve_audit: bool = True) -> bool:
        """Delete a specific interview with cascade.

        Args:
            interview_id: Interview ID to delete
            user_id: User ID (for ownership verification)
            preserve_audit: If True, anonymize LLMCall records

        Returns:
            True if deleted, False if not found or unauthorized

        Cascade deletes (children first for PostgreSQL FK enforcement):
        - Evidence transitions, evidence, contradictions, report, answers, questions
        - The interview
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

        # Handle LLMCall audit records before the interview is deleted
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

        await self.session.execute(
            delete(EvidenceTransition).where(EvidenceTransition.interview_id == interview_id)
        )
        await self.session.execute(
            delete(Evidence).where(Evidence.interview_id == interview_id)
        )
        await self.session.execute(
            delete(Contradiction).where(Contradiction.interview_id == interview_id)
        )
        await self.session.execute(
            delete(InterviewReport).where(InterviewReport.interview_id == interview_id)
        )
        await self.session.execute(
            delete(InterviewAnswer).where(InterviewAnswer.interview_id == interview_id)
        )
        await self.session.execute(
            delete(InterviewQuestion).where(InterviewQuestion.interview_id == interview_id)
        )
        await self.session.execute(delete(Interview).where(Interview.interview_id == interview_id))
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
