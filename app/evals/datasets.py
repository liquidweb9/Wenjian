"""Evaluation dataset loader and schemas."""

import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


# === Scoring Dataset ===

class ExpectedScores(BaseModel):
    technical_correctness: int = Field(ge=0, le=25)
    implementation_depth: int = Field(ge=0, le=20)
    architecture_tradeoffs: int = Field(ge=0, le=15)
    personal_contribution: int = Field(ge=0, le=15)
    production_awareness: int = Field(ge=0, le=15)
    clarity: int = Field(ge=0, le=10)


class ScoringCase(BaseModel):
    case_id: str
    question: str
    answer: str
    expected_scores: ExpectedScores
    reasoning: str
    version: str
    labeled_by: str | None = None
    labeled_at: str | None = None


# === Routing Dataset ===

class RoutingState(BaseModel):
    turn_count: int
    max_turns: int
    current_claim_id: str
    claim_status: str
    current_depth: int
    questions_on_claim: int
    contradictions: list[dict]
    latest_relevance: int
    latest_implementation_depth: int


class RoutingEvaluation(BaseModel):
    dimensions: list[dict]
    strengths: list[str]
    key_missing_points: list[str]


NextAction = Literal[
    "FOLLOW_UP",
    "CLARIFY",
    "INCREASE_DIFFICULTY",
    "SWITCH_CLAIM",
    "SWITCH_TOPIC",
    "COACHING",
    "FINISH"
]


class RoutingCase(BaseModel):
    case_id: str
    state: RoutingState
    latest_evaluation: RoutingEvaluation
    expected_action: NextAction
    reasoning: str
    version: str


# === Evidence Dataset ===

EvidenceStatus = Literal[
    "UNTOUCHED",
    "IN_PROGRESS",
    "PARTIALLY_VERIFIED",
    "VERIFIED",
    "CONTRADICTORY",
    "UNSUPPORTED"
]


class EvidenceCase(BaseModel):
    case_id: str
    claim: str
    verification_point: str
    question: str
    answer: str
    previous_status: EvidenceStatus
    expected_status: EvidenceStatus
    expected_strength: int = Field(ge=0, le=100)
    reasoning: str
    version: str


# === Dataset Loader ===

DatasetType = Literal["scoring", "routing", "evidence"]

DATASETS_DIR = Path(__file__).parent / "datasets"


def load_golden_dataset(
    dataset_type: DatasetType,
    version: str = "v1.0"
) -> list[ScoringCase | RoutingCase | EvidenceCase]:
    """Load a golden dataset for evaluation.

    Args:
        dataset_type: Type of dataset (scoring, routing, evidence)
        version: Dataset version (default: v1.0)

    Returns:
        List of case objects (type depends on dataset_type)

    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If dataset format is invalid
    """
    dataset_path = DATASETS_DIR / dataset_type / f"{version}.jsonl"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}\n"
            f"Available datasets: {list((DATASETS_DIR / dataset_type).glob('*.jsonl'))}"
        )

    cases = []
    case_class = {
        "scoring": ScoringCase,
        "routing": RoutingCase,
        "evidence": EvidenceCase
    }[dataset_type]

    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                case = case_class.model_validate(data)
                cases.append(case)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
            except Exception as e:
                raise ValueError(f"Invalid case at line {line_num}: {e}")

    if not cases:
        raise ValueError(f"Dataset is empty: {dataset_path}")

    return cases


def get_available_versions(dataset_type: DatasetType) -> list[str]:
    """Get list of available versions for a dataset type.

    Args:
        dataset_type: Type of dataset

    Returns:
        List of version strings (e.g., ['v1.0', 'v1.1'])
    """
    dataset_dir = DATASETS_DIR / dataset_type

    if not dataset_dir.exists():
        return []

    versions = [
        path.stem  # Remove .jsonl extension
        for path in dataset_dir.glob("*.jsonl")
    ]

    return sorted(versions)
