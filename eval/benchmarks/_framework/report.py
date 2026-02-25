"""Markdown report generator for AFL benchmark results."""

from __future__ import annotations

import datetime

from .stats import bootstrap_ci, mcnemar_test
from .types import BenchmarkResult

_DISCLAIMER = (
    "These results measure AFL protocol instruction-following effectiveness."
    " Runtime hook enforcement is validated separately."
)


def generate_report(result: BenchmarkResult) -> str:
    """Generate a full markdown report for a BenchmarkResult.

    Includes header, summary metrics table, per-category breakdown,
    statistical CIs, risk-coverage data, raw counts, and disclaimer.
    """
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        f"# Benchmark Report: {result.benchmark_name}",
        "",
        f"**Model:** {result.model}  ",
        f"**Examples:** {result.num_examples}  ",
        f"**Generated:** {ts}",
        "",
        "---",
        "",
        "## Summary Metrics",
        "",
        format_metrics_table(result.metrics),
        "",
    ]

    # Score extraction helpers — work with both AbstentionBench ("correct" bool)
    # and numeric-score benchmarks ("score" or "judge_score" float).
    def _is_correct(s: dict) -> bool:
        if "correct" in s:
            return bool(s["correct"])
        score = float(s.get("score") or s.get("judge_score") or 0.0)
        return score >= 0.5

    def _score_value(s: dict) -> float:
        if "correct" in s:
            return 1.0 if s["correct"] else 0.0
        return float(s.get("score") or s.get("judge_score") or 0.0)

    # Statistical tests
    scored = result.scored_examples
    if scored:
        lines += ["## Statistical Tests", ""]

        baseline_scores = [_score_value(s.scores.get("baseline", {})) for s in scored]
        treatment_scores = [_score_value(s.scores.get("treatment", {})) for s in scored]

        b_mean, b_lo, b_hi = bootstrap_ci(baseline_scores)
        t_mean, t_lo, t_hi = bootstrap_ci(treatment_scores)
        lines.append(
            f"- Baseline accuracy: {b_mean:.3f} (95% CI [{b_lo:.3f}, {b_hi:.3f}])"
        )
        lines.append(
            f"- Treatment accuracy: {t_mean:.3f} (95% CI [{t_lo:.3f}, {t_hi:.3f}])"
        )

        b_correct = [_is_correct(s.scores.get("baseline", {})) for s in scored]
        t_correct = [_is_correct(s.scores.get("treatment", {})) for s in scored]
        mc = mcnemar_test(b_correct, t_correct)
        lines.append(
            f"- McNemar's test (baseline vs treatment): "
            f"p={mc['p_value']:.4f}, "
            f"n_discordant={mc['n_discordant']}"
        )
        lines.append("")

    # Per-category breakdown (uses "category" or "scenario" metadata key)
    categories: dict[str, list] = {}
    for se in scored:
        cat = se.example.metadata.get("category") or se.example.metadata.get("scenario")
        if cat:
            categories.setdefault(cat, []).append(se)

    if categories:
        lines += ["## Per-Category Breakdown", ""]
        lines.append("| Category | N | Baseline Acc | Treatment Acc |")
        lines.append("|----------|---|-------------|---------------|")
        for cat, examples in sorted(categories.items()):
            n = len(examples)
            b_count = sum(
                1 for e in examples if _is_correct(e.scores.get("baseline", {}))
            )
            t_count = sum(
                1 for e in examples if _is_correct(e.scores.get("treatment", {}))
            )
            b_acc = b_count / n if n else 0.0
            t_acc = t_count / n if n else 0.0
            lines.append(f"| {cat} | {n} | {b_acc:.3f} | {t_acc:.3f} |")
        lines.append("")

    # Risk-coverage data
    rc_points: list[tuple[float, float]] = result.metadata.get(
        "risk_coverage_points", []
    )
    if rc_points:
        lines += [
            "## Risk-Coverage Data",
            "",
            "```csv",
            format_risk_coverage_csv(rc_points),
            "```",
            "",
        ]

    # Raw counts
    afl_abstentions = sum(1 for se in scored if se.treatment_response.is_abstention)
    lines += [
        "## Raw Counts",
        "",
        f"- Total examples: {result.num_examples}",
        f"- AFL abstentions (treatment): {afl_abstentions}",
        "",
        "---",
        "",
        f"> **Disclaimer:** {_DISCLAIMER}",
    ]

    return "\n".join(lines)


def format_metrics_table(metrics: dict) -> str:
    """Format a metrics dict as a markdown table.

    Args:
        metrics: Flat or one-level-nested dict of metric name -> value.

    Returns:
        Markdown table string.
    """
    rows: list[tuple[str, str]] = []
    for key, value in metrics.items():
        if isinstance(value, dict):
            for k, v in value.items():
                label = f"{key}.{k}"
                rows.append((label, _fmt_value(v)))
        else:
            rows.append((key, _fmt_value(value)))

    if not rows:
        return "_No metrics._"

    header = "| Metric | Value |"
    sep = "|--------|-------|"
    body = "\n".join(f"| {k} | {v} |" for k, v in rows)
    return f"{header}\n{sep}\n{body}"


def format_risk_coverage_csv(points: list[tuple[float, float]]) -> str:
    """Format (coverage, risk) pairs as CSV.

    Args:
        points: List of (coverage, risk) tuples.

    Returns:
        CSV string with header row.
    """
    lines = ["coverage,risk"]
    for cov, risk in points:
        lines.append(f"{cov:.4f},{risk:.4f}")
    return "\n".join(lines)


def _fmt_value(v: object) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)
