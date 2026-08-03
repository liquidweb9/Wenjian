"""Rubric versioning system for tracking scoring rubric changes.

M2.3: Tracks which rubric version was used for each answer evaluation,
enabling fair cross-version comparison and regression testing.
"""

from dataclasses import dataclass
from typing import Any

from app.persistence.database import async_session_factory
from app.persistence.models import RubricVersion
from sqlalchemy import select
from app.core.ids import new_id


# ============================================================
# Rubric Spec
# ============================================================

@dataclass
class RubricSpec:
    """Rubric specification with version metadata."""
    rubric_name: str
    version: int
    dimension_weights: dict[str, float]
    dimension_descriptors: dict[str, str]
    scoring_guidelines: str | None = None
    level_descriptors: dict[str, Any] | None = None
    max_score: int = 100

    def validate_evaluation(self, evaluation: dict) -> bool:
        """Validate that an evaluation matches this rubric's dimensions.

        Args:
            evaluation: Evaluation dict with dimensions list

        Returns:
            True if valid, False otherwise
        """
        dims = evaluation.get("dimensions", [])
        if not dims:
            return False

        # Check all required dimensions are present
        eval_dimensions = {d.get("dimension") for d in dims}
        required_dimensions = set(self.dimension_weights.keys())

        return required_dimensions.issubset(eval_dimensions)

    def calculate_weighted_score(self, evaluation: dict) -> float:
        """Calculate weighted total score.

        Args:
            evaluation: Evaluation dict with dimensions list

        Returns:
            Weighted score (0-max_score)
        """
        dims = evaluation.get("dimensions", [])
        if not dims:
            return 0.0

        total_weight = sum(self.dimension_weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for d in dims:
            dim_name = d.get("dimension", "")
            weight = self.dimension_weights.get(dim_name, 0)
            score = d.get("score", 0)
            weighted_sum += score * weight

        return weighted_sum / total_weight


# ============================================================
# Rubric Registry
# ============================================================

class RubricRegistry:
    """Registry for managing versioned rubrics."""

    def __init__(self, session_factory=None):
        self._cache: dict[tuple[str, int], RubricSpec] = {}
        self._session_factory = session_factory or async_session_factory

    async def register_rubric(
        self,
        rubric_name: str,
        version: int,
        dimension_weights: dict[str, float],
        dimension_descriptors: dict[str, str],
        scoring_guidelines: str | None = None,
        level_descriptors: dict[str, Any] | None = None,
        max_score: int = 100,
    ) -> str:
        """Register a new rubric version.

        Args:
            rubric_name: Rubric identifier (e.g., "answer_scoring")
            version: Integer version number
            dimension_weights: Weight for each dimension {dimension: weight}
            dimension_descriptors: Description for each dimension
            scoring_guidelines: Additional scoring guidelines
            level_descriptors: Level-specific criteria (optional)
            max_score: Maximum possible score

        Returns:
            rubric_id: Unique ID for this rubric version
        """
        async with self._session_factory() as session:
            # Check if this version already exists
            stmt = select(RubricVersion).where(
                RubricVersion.rubric_name == rubric_name,
                RubricVersion.version == version
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return existing.rubric_id

            # Create new version
            rubric_id = new_id("rubric")
            rubric_version = RubricVersion(
                rubric_id=rubric_id,
                rubric_name=rubric_name,
                version=version,
                dimension_weights=dimension_weights,
                dimension_descriptors=dimension_descriptors,
                scoring_guidelines=scoring_guidelines,
                level_descriptors=level_descriptors,
                max_score=max_score,
                is_active=True,
            )

            session.add(rubric_version)
            await session.commit()

            # Update cache
            spec = RubricSpec(
                rubric_name=rubric_name,
                version=version,
                dimension_weights=dimension_weights,
                dimension_descriptors=dimension_descriptors,
                scoring_guidelines=scoring_guidelines,
                level_descriptors=level_descriptors,
                max_score=max_score,
            )
            self._cache[(rubric_name, version)] = spec

            return rubric_id

    async def get_rubric(self, rubric_name: str, version: int | None = None) -> RubricSpec:
        """Get a rubric by name and version.

        Args:
            rubric_name: Rubric identifier
            version: Specific version (if None, gets latest active version)

        Returns:
            RubricSpec with rubric content and metadata

        Raises:
            ValueError: If rubric not found
        """
        # Check cache first
        if version is not None and (rubric_name, version) in self._cache:
            return self._cache[(rubric_name, version)]

        async with self._session_factory() as session:
            if version is not None:
                # Get specific version
                stmt = select(RubricVersion).where(
                    RubricVersion.rubric_name == rubric_name,
                    RubricVersion.version == version
                )
            else:
                # Get latest active version
                stmt = (
                    select(RubricVersion)
                    .where(
                        RubricVersion.rubric_name == rubric_name,
                        RubricVersion.is_active == True
                    )
                    .order_by(RubricVersion.version.desc())
                    .limit(1)
                )

            result = await session.execute(stmt)
            rubric_version = result.scalar_one_or_none()

            if not rubric_version:
                raise ValueError(
                    f"Rubric not found: rubric_name={rubric_name}, version={version}"
                )

            # Build spec
            spec = RubricSpec(
                rubric_name=rubric_version.rubric_name,
                version=rubric_version.version,
                dimension_weights=rubric_version.dimension_weights,
                dimension_descriptors=rubric_version.dimension_descriptors,
                scoring_guidelines=rubric_version.scoring_guidelines,
                level_descriptors=rubric_version.level_descriptors,
                max_score=rubric_version.max_score,
            )

            # Update cache
            self._cache[(rubric_name, rubric_version.version)] = spec

            return spec

    async def list_versions(self, rubric_name: str) -> list[int]:
        """List all versions for a rubric.

        Args:
            rubric_name: Rubric identifier

        Returns:
            List of version numbers, sorted descending
        """
        async with self._session_factory() as session:
            stmt = (
                select(RubricVersion.version)
                .where(RubricVersion.rubric_name == rubric_name)
                .order_by(RubricVersion.version.desc())
            )
            result = await session.execute(stmt)
            versions = result.scalars().all()
            return list(versions)

    async def compare_versions(
        self,
        rubric_name: str,
        version_a: int,
        version_b: int
    ) -> dict[str, Any]:
        """Compare two rubric versions.

        Args:
            rubric_name: Rubric identifier
            version_a: First version
            version_b: Second version

        Returns:
            Dict with comparison results:
            {
                "weights_changed": bool,
                "dimensions_added": list[str],
                "dimensions_removed": list[str],
                "weight_diff": {dimension: (old_weight, new_weight)},
                "compatible": bool  # Can scores be compared?
            }
        """
        rubric_a = await self.get_rubric(rubric_name, version_a)
        rubric_b = await self.get_rubric(rubric_name, version_b)

        dims_a = set(rubric_a.dimension_weights.keys())
        dims_b = set(rubric_b.dimension_weights.keys())

        added = list(dims_b - dims_a)
        removed = list(dims_a - dims_b)
        common = dims_a & dims_b

        weight_diff = {}
        weights_changed = False
        for dim in common:
            weight_a = rubric_a.dimension_weights[dim]
            weight_b = rubric_b.dimension_weights[dim]
            if weight_a != weight_b:
                weight_diff[dim] = (weight_a, weight_b)
                weights_changed = True

        # Scores are compatible if dimensions are the same
        compatible = len(added) == 0 and len(removed) == 0

        return {
            "weights_changed": weights_changed,
            "dimensions_added": added,
            "dimensions_removed": removed,
            "weight_diff": weight_diff,
            "compatible": compatible,
        }


# Global registry instance
_rubric_registry: RubricRegistry | None = None


def get_rubric_registry() -> RubricRegistry:
    """Get the global rubric registry instance."""
    global _rubric_registry
    if _rubric_registry is None:
        _rubric_registry = RubricRegistry()
    return _rubric_registry


async def initialize_default_rubrics() -> None:
    """Initialize default rubric versions from current system rubrics."""
    from app.interview.rubrics import DIMENSION_WEIGHTS, DIMENSION_DESCRIPTIONS, DEPTH_LEVELS

    registry = get_rubric_registry()

    # Register v1 rubric (current system)
    await registry.register_rubric(
        rubric_name="answer_scoring",
        version=1,
        dimension_weights=DIMENSION_WEIGHTS,
        dimension_descriptors=DIMENSION_DESCRIPTIONS,
        level_descriptors=DEPTH_LEVELS,
        max_score=100,
    )
