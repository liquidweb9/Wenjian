"""Eval gate for CI - blocks merge if regression detected.

M2.3: Compares current prompt/rubric performance against baseline.

Usage:
    python -m app.evals.eval_gate --baseline baseline_results.json

Exit codes:
    0: No regression detected
    1: Regression detected (blocks merge)
    2: Error during evaluation
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.evals.runner import run_baseline_evaluation


# === Regression Thresholds ===

REGRESSION_THRESHOLDS = {
    "scoring": {
        "overall_mae": 2.0,  # MAE increase > 2.0 is regression
        "level_agreement_rate": -0.10,  # 10% drop in agreement is regression
    },
    "routing": {
        "accuracy": -0.15,  # 15% drop in accuracy is regression
        "invalid_route_rate": 0.05,  # 5% increase in invalid routes is regression
    },
    "evidence": {
        "status_accuracy": -0.15,  # 15% drop in accuracy is regression
        "verified_false_positive_rate": 0.10,  # 10% increase in false positives is regression
    },
}


def load_baseline(baseline_path: Path) -> dict[str, Any]:
    """Load baseline evaluation results from file.

    Args:
        baseline_path: Path to baseline JSON file

    Returns:
        Dict with baseline results

    Raises:
        FileNotFoundError: If baseline file doesn't exist
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")

    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_results(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare current results against baseline.

    Args:
        baseline: Baseline evaluation results
        current: Current evaluation results

    Returns:
        Dict with comparison results:
        {
            "regressions": [{"metric": "...", "baseline": 0.9, "current": 0.75, "delta": -0.15}],
            "improvements": [{"metric": "...", "baseline": 0.8, "current": 0.85, "delta": +0.05}],
            "has_regression": bool
        }
    """
    regressions = []
    improvements = []

    # Scoring metrics
    if "scoring" in baseline and "scoring" in current:
        b_scoring = baseline["scoring"]
        c_scoring = current["scoring"]

        # Overall MAE (lower is better)
        mae_delta = c_scoring["overall_mae"] - b_scoring["overall_mae"]
        if mae_delta > REGRESSION_THRESHOLDS["scoring"]["overall_mae"]:
            regressions.append({
                "category": "scoring",
                "metric": "overall_mae",
                "baseline": b_scoring["overall_mae"],
                "current": c_scoring["overall_mae"],
                "delta": mae_delta,
                "threshold": REGRESSION_THRESHOLDS["scoring"]["overall_mae"],
            })
        elif mae_delta < -0.5:  # Improvement
            improvements.append({
                "category": "scoring",
                "metric": "overall_mae",
                "baseline": b_scoring["overall_mae"],
                "current": c_scoring["overall_mae"],
                "delta": mae_delta,
            })

        # Level agreement rate (higher is better)
        agreement_delta = c_scoring["level_agreement_rate"] - b_scoring["level_agreement_rate"]
        if agreement_delta < REGRESSION_THRESHOLDS["scoring"]["level_agreement_rate"]:
            regressions.append({
                "category": "scoring",
                "metric": "level_agreement_rate",
                "baseline": b_scoring["level_agreement_rate"],
                "current": c_scoring["level_agreement_rate"],
                "delta": agreement_delta,
                "threshold": REGRESSION_THRESHOLDS["scoring"]["level_agreement_rate"],
            })
        elif agreement_delta > 0.05:
            improvements.append({
                "category": "scoring",
                "metric": "level_agreement_rate",
                "baseline": b_scoring["level_agreement_rate"],
                "current": c_scoring["level_agreement_rate"],
                "delta": agreement_delta,
            })

    # Routing metrics
    if "routing" in baseline and "routing" in current:
        b_routing = baseline["routing"]
        c_routing = current["routing"]

        # Accuracy (higher is better)
        accuracy_delta = c_routing["accuracy"] - b_routing["accuracy"]
        if accuracy_delta < REGRESSION_THRESHOLDS["routing"]["accuracy"]:
            regressions.append({
                "category": "routing",
                "metric": "accuracy",
                "baseline": b_routing["accuracy"],
                "current": c_routing["accuracy"],
                "delta": accuracy_delta,
                "threshold": REGRESSION_THRESHOLDS["routing"]["accuracy"],
            })
        elif accuracy_delta > 0.05:
            improvements.append({
                "category": "routing",
                "metric": "accuracy",
                "baseline": b_routing["accuracy"],
                "current": c_routing["accuracy"],
                "delta": accuracy_delta,
            })

        # Invalid route rate (lower is better)
        invalid_delta = c_routing["invalid_route_rate"] - b_routing["invalid_route_rate"]
        if invalid_delta > REGRESSION_THRESHOLDS["routing"]["invalid_route_rate"]:
            regressions.append({
                "category": "routing",
                "metric": "invalid_route_rate",
                "baseline": b_routing["invalid_route_rate"],
                "current": c_routing["invalid_route_rate"],
                "delta": invalid_delta,
                "threshold": REGRESSION_THRESHOLDS["routing"]["invalid_route_rate"],
            })

    # Evidence metrics
    if "evidence" in baseline and "evidence" in current:
        b_evidence = baseline["evidence"]
        c_evidence = current["evidence"]

        # Status accuracy (higher is better)
        status_delta = c_evidence["status_accuracy"] - b_evidence["status_accuracy"]
        if status_delta < REGRESSION_THRESHOLDS["evidence"]["status_accuracy"]:
            regressions.append({
                "category": "evidence",
                "metric": "status_accuracy",
                "baseline": b_evidence["status_accuracy"],
                "current": c_evidence["status_accuracy"],
                "delta": status_delta,
                "threshold": REGRESSION_THRESHOLDS["evidence"]["status_accuracy"],
            })
        elif status_delta > 0.05:
            improvements.append({
                "category": "evidence",
                "metric": "status_accuracy",
                "baseline": b_evidence["status_accuracy"],
                "current": c_evidence["status_accuracy"],
                "delta": status_delta,
            })

        # VERIFIED false positive rate (lower is better)
        vfp_delta = c_evidence["verified_false_positive_rate"] - b_evidence["verified_false_positive_rate"]
        if vfp_delta > REGRESSION_THRESHOLDS["evidence"]["verified_false_positive_rate"]:
            regressions.append({
                "category": "evidence",
                "metric": "verified_false_positive_rate",
                "baseline": b_evidence["verified_false_positive_rate"],
                "current": c_evidence["verified_false_positive_rate"],
                "delta": vfp_delta,
                "threshold": REGRESSION_THRESHOLDS["evidence"]["verified_false_positive_rate"],
            })

    return {
        "regressions": regressions,
        "improvements": improvements,
        "has_regression": len(regressions) > 0,
    }


def print_comparison_report(comparison: dict[str, Any]) -> None:
    """Print formatted comparison report.

    Args:
        comparison: Comparison results from compare_results()
    """
    print("\n" + "=" * 60)
    print("EVAL GATE REPORT")
    print("=" * 60 + "\n")

    if comparison["has_regression"]:
        print("❌ REGRESSION DETECTED - Merge blocked\n")
        print("Regressions:")
        for reg in comparison["regressions"]:
            print(f"  • {reg['category']}.{reg['metric']}")
            print(f"    Baseline: {reg['baseline']:.3f}")
            print(f"    Current:  {reg['current']:.3f}")
            print(f"    Delta:    {reg['delta']:+.3f} (threshold: {reg['threshold']:+.3f})")
            print()
    else:
        print("✅ NO REGRESSION - Merge allowed\n")

    if comparison["improvements"]:
        print("Improvements:")
        for imp in comparison["improvements"]:
            print(f"  • {imp['category']}.{imp['metric']}")
            print(f"    Baseline: {imp['baseline']:.3f}")
            print(f"    Current:  {imp['current']:.3f}")
            print(f"    Delta:    {imp['delta']:+.3f}")
            print()

    print("=" * 60)


def save_results(results: dict[str, Any], output_path: Path) -> None:
    """Save evaluation results to file.

    Args:
        results: Evaluation results
        output_path: Path to save results
    """
    # Convert dataclass results to dicts
    serializable = {}
    for category, result in results.items():
        if hasattr(result, "__dict__"):
            serializable[category] = result.__dict__
        else:
            serializable[category] = result

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Eval gate for CI regression testing")
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline evaluation results (JSON)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("current_eval_results.json"),
        help="Path to save current evaluation results",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use real LLM evaluators (default: use mocks)",
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        default="v1.0",
        help="Dataset version to use",
    )

    args = parser.parse_args()

    try:
        # Load baseline
        print(f"Loading baseline from: {args.baseline}")
        baseline = load_baseline(args.baseline)

        # Run current evaluation
        print(f"\nRunning current evaluation (use_llm={args.use_llm})...")
        current_results = run_baseline_evaluation(
            dataset_version=args.dataset_version,
            use_llm=args.use_llm,
        )

        # Save current results
        save_results(current_results, args.output)

        # Compare against baseline
        comparison = compare_results(baseline, current_results)

        # Print report
        print_comparison_report(comparison)

        # Exit with appropriate code
        if comparison["has_regression"]:
            sys.exit(1)  # Block merge
        else:
            sys.exit(0)  # Allow merge

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
