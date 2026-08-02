"""Prompt Registry for version-controlled prompt management.

M2.3: Enables loading prompts by key + version for regression testing.
"""

from dataclasses import dataclass
from typing import Any
from pathlib import Path
import json

from app.persistence.database import async_session_factory
from app.persistence.models import PromptVersion
from sqlalchemy import select
from app.core.ids import new_id


@dataclass
class PromptSpec:
    """Prompt specification with version metadata."""
    task_name: str
    version: int
    system_prompt: str
    input_schema: dict[str, Any] | None = None
    output_model: str | None = None
    rules: str | None = None
    examples: list[dict] | None = None
    forbid_list: list[str] | None = None


class PromptRegistry:
    """Registry for managing versioned prompts."""

    def __init__(self):
        self._cache: dict[tuple[str, int], PromptSpec] = {}

    async def register_prompt(
        self,
        task_name: str,
        version: int,
        system_prompt: str,
        input_schema: dict[str, Any] | None = None,
        output_model: str | None = None,
        rules: str | None = None,
        examples: list[dict] | None = None,
        forbid_list: list[str] | None = None,
    ) -> str:
        """Register a new prompt version.

        Args:
            task_name: Task identifier (e.g., "score_answer", "route_decision")
            version: Integer version number (increments for each change)
            system_prompt: The system prompt text
            input_schema: JSON schema for input validation
            output_model: Pydantic model name for output validation
            rules: Additional rules/constraints
            examples: Few-shot examples
            forbid_list: Forbidden patterns (for prompt injection defense)

        Returns:
            prompt_id: Unique ID for this prompt version
        """
        async with async_session_factory() as session:
            # Check if this version already exists
            stmt = select(PromptVersion).where(
                PromptVersion.task_name == task_name,
                PromptVersion.version == version
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return existing.prompt_id

            # Create new version
            prompt_id = new_id("prompt")
            prompt_version = PromptVersion(
                prompt_id=prompt_id,
                task_name=task_name,
                version=version,
                system_prompt=system_prompt,
                input_schema=input_schema,
                output_model=output_model,
                rules=rules,
                examples=examples,
                forbid_list=forbid_list,
                is_active=True,
            )

            session.add(prompt_version)
            await session.commit()

            # Update cache
            spec = PromptSpec(
                task_name=task_name,
                version=version,
                system_prompt=system_prompt,
                input_schema=input_schema,
                output_model=output_model,
                rules=rules,
                examples=examples,
                forbid_list=forbid_list,
            )
            self._cache[(task_name, version)] = spec

            return prompt_id

    async def get_prompt(self, task_name: str, version: int | None = None) -> PromptSpec:
        """Get a prompt by task name and version.

        Args:
            task_name: Task identifier
            version: Specific version (if None, gets latest active version)

        Returns:
            PromptSpec with prompt content and metadata

        Raises:
            ValueError: If prompt not found
        """
        # Check cache first
        if version is not None and (task_name, version) in self._cache:
            return self._cache[(task_name, version)]

        async with async_session_factory() as session:
            if version is not None:
                # Get specific version
                stmt = select(PromptVersion).where(
                    PromptVersion.task_name == task_name,
                    PromptVersion.version == version
                )
            else:
                # Get latest active version
                stmt = (
                    select(PromptVersion)
                    .where(
                        PromptVersion.task_name == task_name,
                        PromptVersion.is_active == True
                    )
                    .order_by(PromptVersion.version.desc())
                    .limit(1)
                )

            result = await session.execute(stmt)
            prompt_version = result.scalar_one_or_none()

            if not prompt_version:
                raise ValueError(
                    f"Prompt not found: task_name={task_name}, version={version}"
                )

            # Build spec
            spec = PromptSpec(
                task_name=prompt_version.task_name,
                version=prompt_version.version,
                system_prompt=prompt_version.system_prompt,
                input_schema=prompt_version.input_schema,
                output_model=prompt_version.output_model,
                rules=prompt_version.rules,
                examples=prompt_version.examples,
                forbid_list=prompt_version.forbid_list,
            )

            # Update cache
            self._cache[(task_name, prompt_version.version)] = spec

            return spec

    async def list_versions(self, task_name: str) -> list[int]:
        """List all versions for a task.

        Args:
            task_name: Task identifier

        Returns:
            List of version numbers, sorted descending
        """
        async with async_session_factory() as session:
            stmt = (
                select(PromptVersion.version)
                .where(PromptVersion.task_name == task_name)
                .order_by(PromptVersion.version.desc())
            )
            result = await session.execute(stmt)
            versions = result.scalars().all()
            return list(versions)

    async def deactivate_version(self, task_name: str, version: int) -> None:
        """Deactivate a prompt version (marks as inactive, doesn't delete).

        Args:
            task_name: Task identifier
            version: Version to deactivate
        """
        async with async_session_factory() as session:
            stmt = select(PromptVersion).where(
                PromptVersion.task_name == task_name,
                PromptVersion.version == version
            )
            result = await session.execute(stmt)
            prompt_version = result.scalar_one_or_none()

            if prompt_version:
                prompt_version.is_active = False
                await session.commit()

                # Remove from cache
                cache_key = (task_name, version)
                if cache_key in self._cache:
                    del self._cache[cache_key]


# Global registry instance
_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry instance."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


async def load_prompts_from_file(file_path: Path) -> None:
    """Load prompt definitions from a JSON file.

    File format:
    [
        {
            "task_name": "score_answer",
            "version": 1,
            "system_prompt": "...",
            "rules": "...",
            "examples": [...]
        },
        ...
    ]

    Args:
        file_path: Path to JSON file with prompt definitions
    """
    registry = get_prompt_registry()

    with open(file_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    for prompt_def in prompts:
        await registry.register_prompt(
            task_name=prompt_def["task_name"],
            version=prompt_def["version"],
            system_prompt=prompt_def["system_prompt"],
            input_schema=prompt_def.get("input_schema"),
            output_model=prompt_def.get("output_model"),
            rules=prompt_def.get("rules"),
            examples=prompt_def.get("examples"),
            forbid_list=prompt_def.get("forbid_list"),
        )
