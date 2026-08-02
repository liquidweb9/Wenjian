"""Evaluation framework for LLM prompt regression testing."""

from app.evals.datasets import (
    load_golden_dataset,
    get_available_versions,
    ScoringCase,
    RoutingCase,
    EvidenceCase,
    ExpectedScores,
    NextAction,
    EvidenceStatus,
)

from app.evals.runner import (
    run_baseline_evaluation,
    run_scoring_eval,
    run_routing_eval,
    run_evidence_eval,
    ScoringEvalResult,
    RoutingEvalResult,
    EvidenceEvalResult,
)

__all__ = [
    # Dataset loading
    "load_golden_dataset",
    "get_available_versions",
    # Dataset schemas
    "ScoringCase",
    "RoutingCase",
    "EvidenceCase",
    "ExpectedScores",
    "NextAction",
    "EvidenceStatus",
    # Evaluation runners
    "run_baseline_evaluation",
    "run_scoring_eval",
    "run_routing_eval",
    "run_evidence_eval",
    # Result types
    "ScoringEvalResult",
    "RoutingEvalResult",
    "EvidenceEvalResult",
]
