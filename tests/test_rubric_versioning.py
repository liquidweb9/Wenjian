"""Tests for RubricVersioning.

M2.3: Tests rubric versioning, comparison, and weighted scoring.
"""

import pytest
from app.evals.rubric_versioning import (
    RubricRegistry,
    RubricSpec,
    get_rubric_registry,
    initialize_default_rubrics,
)


@pytest.fixture
async def registry():
    """Create a fresh registry for each test."""
    return RubricRegistry()


@pytest.mark.asyncio
async def test_register_and_get_rubric(registry):
    """Test registering and retrieving a rubric."""
    weights = {
        "technical_correctness": 25.0,
        "implementation_depth": 20.0,
        "clarity": 10.0,
    }
    descriptors = {
        "technical_correctness": "Technical accuracy",
        "implementation_depth": "Implementation detail",
        "clarity": "Clear expression",
    }

    rubric_id = await registry.register_rubric(
        rubric_name="test_rubric",
        version=1,
        dimension_weights=weights,
        dimension_descriptors=descriptors,
        max_score=100,
    )

    assert rubric_id.startswith("rubric_")

    spec = await registry.get_rubric("test_rubric", version=1)
    assert spec.rubric_name == "test_rubric"
    assert spec.version == 1
    assert spec.dimension_weights == weights
    assert spec.max_score == 100


@pytest.mark.asyncio
async def test_get_latest_rubric(registry):
    """Test retrieving latest rubric version."""
    weights_v1 = {"dimension_a": 50.0, "dimension_b": 50.0}
    weights_v2 = {"dimension_a": 60.0, "dimension_b": 40.0}
    descriptors = {"dimension_a": "A", "dimension_b": "B"}

    await registry.register_rubric(
        "test_rubric", 1, weights_v1, descriptors
    )
    await registry.register_rubric(
        "test_rubric", 2, weights_v2, descriptors
    )

    spec = await registry.get_rubric("test_rubric")
    assert spec.version == 2
    assert spec.dimension_weights == weights_v2


@pytest.mark.asyncio
async def test_validate_evaluation(registry):
    """Test evaluation validation against rubric."""
    weights = {
        "technical_correctness": 25.0,
        "implementation_depth": 20.0,
        "clarity": 10.0,
    }
    descriptors = {dim: f"Desc {dim}" for dim in weights}

    await registry.register_rubric(
        "test_rubric", 1, weights, descriptors
    )

    spec = await registry.get_rubric("test_rubric", version=1)

    # Valid evaluation
    valid_eval = {
        "dimensions": [
            {"dimension": "technical_correctness", "score": 20},
            {"dimension": "implementation_depth", "score": 15},
            {"dimension": "clarity", "score": 8},
        ]
    }
    assert spec.validate_evaluation(valid_eval) is True

    # Invalid evaluation (missing dimension)
    invalid_eval = {
        "dimensions": [
            {"dimension": "technical_correctness", "score": 20},
        ]
    }
    assert spec.validate_evaluation(invalid_eval) is False

    # Empty evaluation
    empty_eval = {"dimensions": []}
    assert spec.validate_evaluation(empty_eval) is False


@pytest.mark.asyncio
async def test_calculate_weighted_score(registry):
    """Test weighted score calculation."""
    weights = {
        "technical_correctness": 25.0,
        "implementation_depth": 20.0,
        "clarity": 10.0,
    }
    descriptors = {dim: f"Desc {dim}" for dim in weights}

    await registry.register_rubric(
        "test_rubric", 1, weights, descriptors
    )

    spec = await registry.get_rubric("test_rubric", version=1)

    evaluation = {
        "dimensions": [
            {"dimension": "technical_correctness", "score": 20},
            {"dimension": "implementation_depth", "score": 15},
            {"dimension": "clarity", "score": 8},
        ]
    }

    # Expected: (20*25 + 15*20 + 8*10) / (25+20+10) = (500 + 300 + 80) / 55 = 880/55 = 16.0
    weighted_score = spec.calculate_weighted_score(evaluation)
    assert abs(weighted_score - 16.0) < 0.01


@pytest.mark.asyncio
async def test_list_versions(registry):
    """Test listing rubric versions."""
    weights = {"dim_a": 50.0, "dim_b": 50.0}
    descriptors = {"dim_a": "A", "dim_b": "B"}

    await registry.register_rubric("rubric_a", 1, weights, descriptors)
    await registry.register_rubric("rubric_a", 2, weights, descriptors)
    await registry.register_rubric("rubric_a", 3, weights, descriptors)

    versions = await registry.list_versions("rubric_a")
    assert versions == [3, 2, 1]


@pytest.mark.asyncio
async def test_compare_versions(registry):
    """Test comparing two rubric versions."""
    weights_v1 = {
        "technical_correctness": 25.0,
        "implementation_depth": 20.0,
        "clarity": 10.0,
    }
    weights_v2 = {
        "technical_correctness": 30.0,  # Changed weight
        "implementation_depth": 20.0,
        "architecture": 15.0,  # New dimension
        # clarity removed
    }
    descriptors = {dim: f"Desc {dim}" for dim in set(list(weights_v1.keys()) + list(weights_v2.keys()))}

    await registry.register_rubric("test_rubric", 1, weights_v1, descriptors)
    await registry.register_rubric("test_rubric", 2, weights_v2, descriptors)

    comparison = await registry.compare_versions("test_rubric", 1, 2)

    assert comparison["weights_changed"] is True
    assert "architecture" in comparison["dimensions_added"]
    assert "clarity" in comparison["dimensions_removed"]
    assert comparison["weight_diff"]["technical_correctness"] == (25.0, 30.0)
    assert comparison["compatible"] is False  # Different dimensions


@pytest.mark.asyncio
async def test_compatible_versions(registry):
    """Test that versions with same dimensions are compatible."""
    weights_v1 = {"dim_a": 50.0, "dim_b": 50.0}
    weights_v2 = {"dim_a": 60.0, "dim_b": 40.0}  # Only weights changed
    descriptors = {"dim_a": "A", "dim_b": "B"}

    await registry.register_rubric("test_rubric", 1, weights_v1, descriptors)
    await registry.register_rubric("test_rubric", 2, weights_v2, descriptors)

    comparison = await registry.compare_versions("test_rubric", 1, 2)

    assert comparison["compatible"] is True
    assert comparison["dimensions_added"] == []
    assert comparison["dimensions_removed"] == []


@pytest.mark.asyncio
async def test_rubric_not_found(registry):
    """Test error when rubric doesn't exist."""
    with pytest.raises(ValueError, match="Rubric not found"):
        await registry.get_rubric("nonexistent_rubric")


@pytest.mark.asyncio
async def test_duplicate_registration(registry):
    """Test that registering same version twice returns same ID."""
    weights = {"dim_a": 100.0}
    descriptors = {"dim_a": "A"}

    rubric_id_1 = await registry.register_rubric(
        "test_rubric", 1, weights, descriptors
    )
    rubric_id_2 = await registry.register_rubric(
        "test_rubric", 1, weights, descriptors
    )

    assert rubric_id_1 == rubric_id_2


@pytest.mark.asyncio
async def test_global_registry_singleton():
    """Test that get_rubric_registry returns singleton."""
    reg1 = get_rubric_registry()
    reg2 = get_rubric_registry()

    assert reg1 is reg2


@pytest.mark.asyncio
async def test_initialize_default_rubrics():
    """Test initializing default rubrics from system."""
    await initialize_default_rubrics()

    registry = get_rubric_registry()
    spec = await registry.get_rubric("answer_scoring", version=1)

    # Should have the standard 6 dimensions
    assert "technical_correctness" in spec.dimension_weights
    assert "implementation_depth" in spec.dimension_weights
    assert "architecture_tradeoffs" in spec.dimension_weights
    assert "personal_contribution" in spec.dimension_weights
    assert "production_awareness" in spec.dimension_weights
    assert "clarity" in spec.dimension_weights

    assert spec.max_score == 100
