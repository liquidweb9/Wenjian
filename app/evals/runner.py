"""Baseline evaluation runner for Phase 1 prompt/rubric regression testing."""

import statistics
from dataclasses import dataclass
from typing import Literal

from app.evals.datasets import (
    load_golden_dataset,
    ScoringCase,
    RoutingCase,
    EvidenceCase,
    NextAction,
    EvidenceStatus,
)


# === Evaluation Results ===

@dataclass
class ScoringEvalResult:
    """Results from scoring evaluation."""
    total_cases: int
    mae_per_dimension: dict[str, float]
    overall_mae: float
    level_agreement_rate: float  # ±1 level tolerance
    dimension_miss_rate: dict[str, float]  # Dimension scored 0 when should be >0

    def summary(self) -> str:
        lines = [
            f"Scoring Evaluation Results ({self.total_cases} cases)",
            f"  Overall MAE: {self.overall_mae:.2f}",
            f"  Level Agreement Rate: {self.level_agreement_rate:.1%}",
            "  MAE per dimension:",
        ]
        for dim, mae in self.mae_per_dimension.items():
            miss_rate = self.dimension_miss_rate.get(dim, 0.0)
            lines.append(f"    {dim}: {mae:.2f} (miss rate: {miss_rate:.1%})")
        return "\n".join(lines)


@dataclass
class RoutingEvalResult:
    """Results from routing evaluation."""
    total_cases: int
    accuracy: float  # Exact match rate
    invalid_route_rate: float  # Non-enum outputs
    premature_switch_rate: float  # Switches claim when should follow-up
    confusion_matrix: dict[tuple[NextAction, NextAction], int]  # (expected, actual) -> count

    def summary(self) -> str:
        lines = [
            f"Routing Evaluation Results ({self.total_cases} cases)",
            f"  Accuracy: {self.accuracy:.1%}",
            f"  Invalid Route Rate: {self.invalid_route_rate:.1%}",
            f"  Premature Switch Rate: {self.premature_switch_rate:.1%}",
        ]
        return "\n".join(lines)


@dataclass
class EvidenceEvalResult:
    """Results from evidence evaluation."""
    total_cases: int
    status_accuracy: float  # Exact match rate
    verified_false_positive_rate: float  # Claims VERIFIED without sufficient evidence
    unsupported_false_negative_rate: float  # Marks UNSUPPORTED too early
    contradiction_precision: float
    contradiction_recall: float
    strength_mae: float  # Mean absolute error on strength scores

    def summary(self) -> str:
        lines = [
            f"Evidence Evaluation Results ({self.total_cases} cases)",
            f"  Status Accuracy: {self.status_accuracy:.1%}",
            f"  VERIFIED False Positive Rate: {self.verified_false_positive_rate:.1%}",
            f"  UNSUPPORTED False Negative Rate: {self.unsupported_false_negative_rate:.1%}",
            f"  Contradiction Precision: {self.contradiction_precision:.1%}",
            f"  Contradiction Recall: {self.contradiction_recall:.1%}",
            f"  Strength MAE: {self.strength_mae:.2f}",
        ]
        return "\n".join(lines)


# === Mock Evaluators (will be replaced with real LLM calls in M2.3) ===

def mock_score_answer(question: str, answer: str) -> dict[str, int]:
    """Mock scoring function - returns dummy scores.

    In M2.3, this will be replaced with actual LLM scoring call.
    """
    # For baseline testing, return expected scores from first case
    # Real implementation will call LLM with current prompt version
    return {
        "technical_correctness": 18,
        "implementation_depth": 12,
        "architecture_tradeoffs": 8,
        "personal_contribution": 10,
        "production_awareness": 10,
        "clarity": 8,
    }


def mock_route_decision(state: dict, evaluation: dict) -> NextAction:
    """Mock routing function - returns dummy action.

    In M2.3, this will be replaced with actual routing logic.
    """
    # For baseline testing, return FOLLOW_UP
    # Real implementation will use rules + LLM suggestion
    return "FOLLOW_UP"


def mock_evidence_status(
    claim: str,
    verification_point: str,
    answer: str,
    previous_status: EvidenceStatus
) -> tuple[EvidenceStatus, int]:
    """Mock evidence evaluation - returns dummy status and strength.

    In M2.3, this will be replaced with actual evidence state machine.
    """
    # For baseline testing, return IN_PROGRESS
    # Real implementation will use state machine transitions
    return ("IN_PROGRESS", 50)


# === Evaluation Runners ===

def run_scoring_eval(
    cases: list[ScoringCase],
    scorer_fn=mock_score_answer
) -> ScoringEvalResult:
    """Run scoring evaluation on golden dataset.

    Args:
        cases: List of scoring test cases
        scorer_fn: Function that scores an answer (for testing, can inject mock)

    Returns:
        ScoringEvalResult with metrics
    """
    dimension_names = [
        "technical_correctness",
        "implementation_depth",
        "architecture_tradeoffs",
        "personal_contribution",
        "production_awareness",
        "clarity"
    ]

    dimension_errors = {dim: [] for dim in dimension_names}
    dimension_misses = {dim: [] for dim in dimension_names}
    level_agreements = []

    for case in cases:
        actual_scores = scorer_fn(case.question, case.answer)
        expected = case.expected_scores.model_dump()

        # Calculate errors per dimension
        for dim in dimension_names:
            exp_score = expected[dim]
            act_score = actual_scores.get(dim, 0)

            error = abs(exp_score - act_score)
            dimension_errors[dim].append(error)

            # Check for miss (scored 0 when should be >0)
            if exp_score > 0 and act_score == 0:
                dimension_misses[dim].append(1)
            else:
                dimension_misses[dim].append(0)

            # Check level agreement (±1 level tolerance)
            # Assuming levels are: 0-20% = L1, 20-40% = L2, etc.
            max_score = {"technical_correctness": 25, "implementation_depth": 20,
                        "architecture_tradeoffs": 15, "personal_contribution": 15,
                        "production_awareness": 15, "clarity": 10}[dim]

            exp_level = int(exp_score / max_score * 5)  # 0-5
            act_level = int(act_score / max_score * 5)

            if abs(exp_level - act_level) <= 1:
                level_agreements.append(1)
            else:
                level_agreements.append(0)

    # Calculate metrics
    mae_per_dimension = {
        dim: statistics.mean(errors) if errors else 0.0
        for dim, errors in dimension_errors.items()
    }

    all_errors = [e for errors in dimension_errors.values() for e in errors]
    overall_mae = statistics.mean(all_errors) if all_errors else 0.0

    level_agreement_rate = statistics.mean(level_agreements) if level_agreements else 0.0

    dimension_miss_rate = {
        dim: statistics.mean(misses) if misses else 0.0
        for dim, misses in dimension_misses.items()
    }

    return ScoringEvalResult(
        total_cases=len(cases),
        mae_per_dimension=mae_per_dimension,
        overall_mae=overall_mae,
        level_agreement_rate=level_agreement_rate,
        dimension_miss_rate=dimension_miss_rate,
    )


def run_routing_eval(
    cases: list[RoutingCase],
    router_fn=mock_route_decision
) -> RoutingEvalResult:
    """Run routing evaluation on golden dataset.

    Args:
        cases: List of routing test cases
        router_fn: Function that decides next action

    Returns:
        RoutingEvalResult with metrics
    """
    exact_matches = []
    invalid_routes = []
    premature_switches = []
    confusion_matrix: dict[tuple[NextAction, NextAction], int] = {}

    for case in cases:
        state_dict = case.state.model_dump()
        eval_dict = case.latest_evaluation.model_dump()

        actual_action = router_fn(state_dict, eval_dict)
        expected_action = case.expected_action

        # Exact match
        if actual_action == expected_action:
            exact_matches.append(1)
        else:
            exact_matches.append(0)

        # Invalid route (not in enum)
        valid_actions = {"FOLLOW_UP", "CLARIFY", "INCREASE_DIFFICULTY",
                        "SWITCH_CLAIM", "SWITCH_TOPIC", "COACHING", "FINISH"}
        if actual_action not in valid_actions:
            invalid_routes.append(1)
        else:
            invalid_routes.append(0)

        # Premature switch (switches when should follow-up)
        if expected_action == "FOLLOW_UP" and actual_action == "SWITCH_CLAIM":
            premature_switches.append(1)
        else:
            premature_switches.append(0)

        # Confusion matrix
        key = (expected_action, actual_action)
        confusion_matrix[key] = confusion_matrix.get(key, 0) + 1

    return RoutingEvalResult(
        total_cases=len(cases),
        accuracy=statistics.mean(exact_matches) if exact_matches else 0.0,
        invalid_route_rate=statistics.mean(invalid_routes) if invalid_routes else 0.0,
        premature_switch_rate=statistics.mean(premature_switches) if premature_switches else 0.0,
        confusion_matrix=confusion_matrix,
    )


def run_evidence_eval(
    cases: list[EvidenceCase],
    evaluator_fn=mock_evidence_status
) -> EvidenceEvalResult:
    """Run evidence evaluation on golden dataset.

    Args:
        cases: List of evidence test cases
        evaluator_fn: Function that evaluates evidence status

    Returns:
        EvidenceEvalResult with metrics
    """
    status_matches = []
    strength_errors = []

    verified_fps = []  # False positives (predicted VERIFIED incorrectly)
    unsupported_fns = []  # False negatives (predicted UNSUPPORTED too early)

    contradiction_tp = 0  # True positives
    contradiction_fp = 0  # False positives
    contradiction_fn = 0  # False negatives

    for case in cases:
        actual_status, actual_strength = evaluator_fn(
            case.claim,
            case.verification_point,
            case.answer,
            case.previous_status
        )

        expected_status = case.expected_status
        expected_strength = case.expected_strength

        # Status accuracy
        if actual_status == expected_status:
            status_matches.append(1)
        else:
            status_matches.append(0)

        # Strength MAE
        strength_errors.append(abs(expected_strength - actual_strength))

        # VERIFIED false positive
        if actual_status == "VERIFIED" and expected_status != "VERIFIED":
            verified_fps.append(1)
        else:
            verified_fps.append(0)

        # UNSUPPORTED false negative
        if actual_status == "UNSUPPORTED" and expected_status in ["IN_PROGRESS", "PARTIALLY_VERIFIED"]:
            unsupported_fns.append(1)
        else:
            unsupported_fns.append(0)

        # Contradiction detection
        if expected_status == "CONTRADICTORY":
            if actual_status == "CONTRADICTORY":
                contradiction_tp += 1
            else:
                contradiction_fn += 1
        else:
            if actual_status == "CONTRADICTORY":
                contradiction_fp += 1

    # Calculate contradiction metrics
    contradiction_precision = (
        contradiction_tp / (contradiction_tp + contradiction_fp)
        if (contradiction_tp + contradiction_fp) > 0 else 0.0
    )

    contradiction_recall = (
        contradiction_tp / (contradiction_tp + contradiction_fn)
        if (contradiction_tp + contradiction_fn) > 0 else 0.0
    )

    return EvidenceEvalResult(
        total_cases=len(cases),
        status_accuracy=statistics.mean(status_matches) if status_matches else 0.0,
        verified_false_positive_rate=statistics.mean(verified_fps) if verified_fps else 0.0,
        unsupported_false_negative_rate=statistics.mean(unsupported_fns) if unsupported_fns else 0.0,
        contradiction_precision=contradiction_precision,
        contradiction_recall=contradiction_recall,
        strength_mae=statistics.mean(strength_errors) if strength_errors else 0.0,
    )


# === Main Baseline Runner ===

def run_baseline_evaluation(
    dataset_version: str = "v1.0",
    use_llm: bool = False,
    prompt_version: int | None = None,
    rubric_version: int | None = None,
) -> dict:
    """Run complete baseline evaluation across all dataset types.

    Args:
        dataset_version: Version of datasets to use
        use_llm: If True, use real LLM evaluators; if False, use mocks
        prompt_version: Specific prompt version (None = latest)
        rubric_version: Specific rubric version (None = latest)

    Returns:
        Dict with results for each dataset type
    """
    print(f"\n{'='*60}")
    mode = "LLM-based" if use_llm else "Mock-based"
    print(f"Phase 2 Evaluation ({mode}, Dataset v{dataset_version})")
    if use_llm:
        print(f"  Prompt version: {prompt_version or 'latest'}")
        print(f"  Rubric version: {rubric_version or 'latest'}")
    print(f"{'='*60}\n")

    results = {}

    # Select evaluator functions
    if use_llm:
        import asyncio
        from app.evals.evaluators import (
            score_answer_with_llm,
            route_decision_with_llm,
            evaluate_evidence_with_llm,
        )

        # Wrap async functions for sync runner
        def scoring_fn(question: str, answer: str) -> dict[str, int]:
            return asyncio.run(
                score_answer_with_llm(question, answer, prompt_version, rubric_version)
            )

        def routing_fn(state: dict, evaluation: dict) -> NextAction:
            return asyncio.run(
                route_decision_with_llm(state, evaluation, prompt_version)
            )

        def evidence_fn(claim: str, vp: str, answer: str, prev: EvidenceStatus):
            return asyncio.run(
                evaluate_evidence_with_llm(claim, vp, answer, prev, prompt_version)
            )
    else:
        scoring_fn = mock_score_answer
        routing_fn = mock_route_decision
        evidence_fn = mock_evidence_status

    # Scoring evaluation
    print("Running scoring evaluation...")
    scoring_cases = load_golden_dataset("scoring", version=dataset_version)
    scoring_result = run_scoring_eval(scoring_cases, scorer_fn=scoring_fn)
    results["scoring"] = scoring_result
    print(scoring_result.summary())
    print()

    # Routing evaluation
    print("Running routing evaluation...")
    routing_cases = load_golden_dataset("routing", version=dataset_version)
    routing_result = run_routing_eval(routing_cases, router_fn=routing_fn)
    results["routing"] = routing_result
    print(routing_result.summary())
    print()

    # Evidence evaluation
    print("Running evidence evaluation...")
    evidence_cases = load_golden_dataset("evidence", version=dataset_version)
    evidence_result = run_evidence_eval(evidence_cases, evaluator_fn=evidence_fn)
    results["evidence"] = evidence_result
    print(evidence_result.summary())
    print()

    print(f"{'='*60}")
    print("Evaluation complete!")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    import sys

    # Check if --llm flag is provided
    use_llm = "--llm" in sys.argv

    # Run baseline evaluation
    results = run_baseline_evaluation(use_llm=use_llm)
