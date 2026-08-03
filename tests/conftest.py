"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
import tempfile
import os
import time
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.persistence.database import Base


# Generate unique timestamp for test data
@pytest.fixture(scope="session", autouse=True)
def setup_test_timestamp():
    """Set up a unique timestamp for this test session."""
    pytest.timestamp = int(time.time() * 1000)
# Import all models to ensure they're registered with Base.metadata
from app.persistence.models import (
    User, ResumeSource, ResumeRevision, ResumeBlock, ResumeProfile, ResumeClaim,
    Interview, InterviewQuestion, InterviewAnswer, InterviewReport,
    JobTarget, JobRequirement, Competency,
    VerificationPoint, Evidence, EvidenceTransition, Contradiction,
    AbilityObservation, AbilityProfile, TrainingTask,
    AnswerVersion,
    LLMCall, PromptVersion, RubricVersion,
    ClaimCompetencyMapping, ClaimRequirementMapping,
)


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for tests with temporary file database."""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    TEST_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables and clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Remove temporary file
    try:
        os.unlink(db_path)
    except:
        pass


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async session for tests."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()
