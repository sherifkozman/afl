"""CLI runner for AbstentionBench AFL evaluation.

Usage:
    python -m eval.benchmarks.cli abstentionbench [options]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.benchmarks._framework.protocol import (
    build_system_prompt,
    generate_response,
)
from eval.benchmarks._framework.report import generate_report
from eval.benchmarks._framework.types import BenchmarkResult, ScoredExample

from .adapter import AbstentionBenchAdapter


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run AbstentionBench AFL evaluation",
    )
    p.add_argument("--model", default="google/gemini-2.5-flash")
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap examples per split (Phase 0 smoke test)",
    )
    p.add_argument(
        "--fast-subset",
        action="store_true",
        help="Use 100-per-dataset fast-subset indices (Phase 1)",
    )
    p.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="Filter to scenario(s); repeatable",
    )
    p.add_argument(
        "--split", default="all", help="Dataset split to load (default: all)"
    )
    p.add_argument("--temperature", type=float, default=0.0)

    # Client configuration.
    p.add_argument("--vertex", action="store_true")
    p.add_argument("--project", default=None)
    p.add_argument("--location", default="us-central1")
    p.add_argument("--base-url", default=None)
    p.add_argument("--api-key", default=None)

    # Output.
    p.add_argument("--output", default=None, help="Path for markdown report")
    p.add_argument("--output-json", default=None, help="Path for JSON results")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    adapter = AbstentionBenchAdapter(scenarios=args.scenario)

    print(
        f"Loading AbstentionBench (split={args.split}, limit={args.limit}, "
        f"fast_subset={args.fast_subset}) ...",
        flush=True,
    )

    examples = adapter.load_examples(
        split=args.split,
        limit=args.limit,
        fast_subset=args.fast_subset,
    )
    print(f"Loaded {len(examples)} examples.", flush=True)

    if not examples:
        print("No examples to evaluate. Exiting.", file=sys.stderr)
        sys.exit(1)

    client_kwargs = dict(
        model=args.model,
        vertex=args.vertex,
        project=args.project,
        location=args.location,
        base_url=args.base_url,
        api_key=args.api_key,
        temperature=args.temperature,
    )

    scored: list[ScoredExample] = []

    for i, ex in enumerate(examples, 1):
        prompt = adapter.format_prompt(ex)
        print(f"[{i}/{len(examples)}] {ex.id} ...", end=" ", flush=True)

        # Baseline: no AFL protocol.
        baseline = generate_response(
            prompt=prompt,
            system="",
            **client_kwargs,
        )
        baseline_score = adapter.score_response(ex, baseline)

        # Treatment: with AFL protocol.
        treatment = generate_response(
            prompt=prompt,
            system=build_system_prompt(with_afl=True),
            **client_kwargs,
        )
        treatment_score = adapter.score_response(ex, treatment)

        se = ScoredExample(
            example=ex,
            baseline_response=baseline,
            treatment_response=treatment,
            scores={"baseline": baseline_score, "treatment": treatment_score},
        )
        scored.append(se)

        b_tag = "ABSTAIN" if baseline_score["abstained"] else "ANSWER"
        t_tag = "ABSTAIN" if treatment_score["abstained"] else "ANSWER"
        label = "should_abstain" if ex.ground_truth else "should_answer"
        print(f"baseline={b_tag}  treatment={t_tag}  ({label})", flush=True)

    # Aggregate.
    metrics = adapter.aggregate(scored)

    result = BenchmarkResult(
        benchmark_name="AbstentionBench",
        model=args.model,
        num_examples=len(scored),
        metrics=metrics,
        scored_examples=scored,
    )

    # Print summary to stdout.
    _print_summary(metrics)

    # Write outputs.
    if args.output:
        report = generate_report(result)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\nMarkdown report written to {args.output}", flush=True)

    if args.output_json:
        Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
        json_data = {
            "benchmark": "AbstentionBench",
            "model": args.model,
            "num_examples": len(scored),
            "metrics": metrics,
        }
        Path(args.output_json).write_text(
            json.dumps(json_data, indent=2), encoding="utf-8"
        )
        print(f"JSON results written to {args.output_json}", flush=True)


def _print_summary(metrics: dict) -> None:
    print("\n" + "=" * 60)
    print("AbstentionBench Results")
    print("=" * 60)

    for arm in ("baseline", "treatment"):
        m = metrics.get(arm, {})
        print(f"\n  {arm.upper()}:")
        print(f"    Accuracy:        {m.get('accuracy', 0):.4f}")
        print(f"    Precision:       {m.get('precision', 0):.4f}")
        print(f"    Recall:          {m.get('recall', 0):.4f}")
        print(f"    F1:              {m.get('f1', 0):.4f}")
        print(f"    Over-refusal:    {m.get('over_refusal_rate', 0):.4f}")
        print(f"    Abstention rate: {m.get('abstention_rate', 0):.4f}")

    delta = metrics.get("recovery_delta", 0)
    print(f"\n  Recovery Delta (treatment - baseline recall): {delta:+.4f}")

    # Per-scenario.
    per_scenario = metrics.get("per_scenario", {})
    if per_scenario:
        print(f"\n  {'SCENARIO':<25} {'B-F1':>6} {'T-F1':>6} {'Delta':>7}")
        print("  " + "-" * 46)
        for scenario, arms in sorted(per_scenario.items()):
            bf1 = arms.get("baseline", {}).get("f1", 0)
            tf1 = arms.get("treatment", {}).get("f1", 0)
            d = tf1 - bf1
            print(f"  {scenario:<25} {bf1:6.4f} {tf1:6.4f} {d:+7.4f}")

    print()
