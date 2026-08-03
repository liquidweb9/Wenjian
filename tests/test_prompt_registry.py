"""Tests for PromptRegistry.

M2.3: Tests prompt versioning, loading, and registration.
"""

import pytest
from contextlib import asynccontextmanager
from app.evals.prompt_registry import (
    PromptRegistry,
    PromptSpec,
    get_prompt_registry,
)


@pytest.fixture
async def registry(async_engine):
    """Create a fresh registry for each test with test database session."""
    # Create a session maker that uses the test engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return PromptRegistry(session_factory=session_factory)


@pytest.mark.asyncio
async def test_register_and_get_prompt(registry):
    """Test registering and retrieving a prompt."""
    prompt_id = await registry.register_prompt(
        task_name="test_task",
        version=1,
        system_prompt="You are a helpful assistant.",
        rules="Be concise.",
    )

    assert prompt_id.startswith("prompt_")

    # Retrieve by specific version
    spec = await registry.get_prompt("test_task", version=1)
    assert spec.task_name == "test_task"
    assert spec.version == 1
    assert spec.system_prompt == "You are a helpful assistant."
    assert spec.rules == "Be concise."


@pytest.mark.asyncio
async def test_get_latest_prompt(registry):
    """Test retrieving latest prompt version."""
    # Register multiple versions
    await registry.register_prompt(
        task_name="test_task",
        version=1,
        system_prompt="Version 1",
    )
    await registry.register_prompt(
        task_name="test_task",
        version=2,
        system_prompt="Version 2",
    )
    await registry.register_prompt(
        task_name="test_task",
        version=3,
        system_prompt="Version 3",
    )

    # Get latest (should be v3)
    spec = await registry.get_prompt("test_task")
    assert spec.version == 3
    assert spec.system_prompt == "Version 3"


@pytest.mark.asyncio
async def test_list_versions(registry):
    """Test listing all versions for a task."""
    await registry.register_prompt("task_a", 1, "Prompt v1")
    await registry.register_prompt("task_a", 2, "Prompt v2")
    await registry.register_prompt("task_a", 3, "Prompt v3")

    versions = await registry.list_versions("task_a")
    assert versions == [3, 2, 1]  # Descending order


@pytest.mark.asyncio
async def test_deactivate_version(registry):
    """Test deactivating a prompt version."""
    await registry.register_prompt("task_b", 1, "Active prompt")
    await registry.register_prompt("task_b", 2, "Another prompt")

    # Deactivate v1
    await registry.deactivate_version("task_b", 1)

    # Latest should now be v2
    spec = await registry.get_prompt("task_b")
    assert spec.version == 2

    # Can still get v1 by explicit version
    spec_v1 = await registry.get_prompt("task_b", version=1)
    assert spec_v1.version == 1


@pytest.mark.asyncio
async def test_prompt_not_found(registry):
    """Test error when prompt doesn't exist."""
    with pytest.raises(ValueError, match="Prompt not found"):
        await registry.get_prompt("nonexistent_task")


@pytest.mark.asyncio
async def test_duplicate_registration(registry):
    """Test that registering same version twice returns same ID."""
    prompt_id_1 = await registry.register_prompt(
        task_name="task_c",
        version=1,
        system_prompt="Test prompt",
    )

    prompt_id_2 = await registry.register_prompt(
        task_name="task_c",
        version=1,
        system_prompt="Test prompt",
    )

    # Should return same ID
    assert prompt_id_1 == prompt_id_2


@pytest.mark.asyncio
async def test_prompt_with_examples(registry):
    """Test registering prompt with examples."""
    examples = [
        {"input": "Question 1", "output": "Answer 1"},
        {"input": "Question 2", "output": "Answer 2"},
    ]

    await registry.register_prompt(
        task_name="task_with_examples",
        version=1,
        system_prompt="Test",
        examples=examples,
    )

    spec = await registry.get_prompt("task_with_examples", version=1)
    assert spec.examples == examples


@pytest.mark.asyncio
async def test_prompt_caching(registry):
    """Test that prompts are cached after first retrieval."""
    await registry.register_prompt("cached_task", 1, "Cached prompt")

    # First retrieval (from DB)
    spec1 = await registry.get_prompt("cached_task", version=1)

    # Second retrieval (from cache)
    spec2 = await registry.get_prompt("cached_task", version=1)

    assert spec1.system_prompt == spec2.system_prompt
    assert ("cached_task", 1) in registry._cache


@pytest.mark.asyncio
async def test_global_registry_singleton():
    """Test that get_prompt_registry returns singleton."""
    reg1 = get_prompt_registry()
    reg2 = get_prompt_registry()

    assert reg1 is reg2
