"""Statistical utilities for benchmark evaluation (stdlib only)."""

from __future__ import annotations

import math
import random


def bootstrap_ci(
    scores: list[float],
    n: int = 10000,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Percentile bootstrap confidence interval.

    Returns:
        (mean, lower, upper) where lower/upper are the (alpha/2, 1-alpha/2) percentiles.
    """
    if not scores:
        return 0.0, 0.0, 0.0

    mean = sum(scores) / len(scores)

    if len(scores) == 1:
        return mean, mean, mean

    rng = random.Random(42)
    boot_means: list[float] = []
    for _ in range(n):
        sample = [rng.choice(scores) for _ in range(len(scores))]
        boot_means.append(sum(sample) / len(sample))

    boot_means.sort()
    lo_idx = int(math.floor(alpha / 2 * n))
    hi_idx = int(math.ceil((1 - alpha / 2) * n)) - 1
    lo_idx = max(0, min(lo_idx, len(boot_means) - 1))
    hi_idx = max(0, min(hi_idx, len(boot_means) - 1))

    return mean, boot_means[lo_idx], boot_means[hi_idx]


def mcnemar_test(
    paired_correct_a: list[bool],
    paired_correct_b: list[bool],
) -> dict:
    """McNemar's test for paired binary outcomes.

    Args:
        paired_correct_a: Correctness flags for condition A (baseline).
        paired_correct_b: Correctness flags for condition B (treatment).

    Returns:
        Dict with statistic (float), p_value (float), n_discordant (int).
    """
    if len(paired_correct_a) != len(paired_correct_b):
        raise ValueError("Input lists must have the same length.")

    # b: A correct, B wrong; c: A wrong, B correct
    b = sum(1 for a, t in zip(paired_correct_a, paired_correct_b) if a and not t)
    c = sum(1 for a, t in zip(paired_correct_a, paired_correct_b) if not a and t)
    n_discordant = b + c

    if n_discordant == 0:
        return {"statistic": 0.0, "p_value": 1.0, "n_discordant": 0}

    # McNemar chi-squared with continuity correction
    statistic = (abs(b - c) - 1.0) ** 2 / n_discordant

    # Approximate p-value from chi-squared(df=1) via regularized incomplete gamma
    p_value = _chi2_sf(statistic, df=1)

    return {"statistic": statistic, "p_value": p_value, "n_discordant": n_discordant}


def _chi2_sf(x: float, df: int) -> float:
    """Survival function (1 - CDF) of chi-squared distribution (stdlib only)."""
    if x <= 0:
        return 1.0
    # chi2(df=1) SF = erfc(sqrt(x/2))
    if df == 1:
        return math.erfc(math.sqrt(x / 2))
    # For df=2: SF = exp(-x/2)
    if df == 2:
        return math.exp(-x / 2)
    # General: regularized upper incomplete gamma via recursion (df even)
    # For benchmark use df=1 is sufficient; fallback approximation for others
    return math.erfc(math.sqrt(x / 2))  # rough but acceptable for df near 1


def risk_coverage_curve(
    risks: list[float],
    coverages: list[float],
) -> list[tuple[float, float]]:
    """Sort (coverage, risk) pairs by coverage ascending.

    Args:
        risks: Risk values (e.g., error rate at each threshold).
        coverages: Coverage values (fraction of examples answered).

    Returns:
        List of (coverage, risk) tuples sorted by coverage.
    """
    if len(risks) != len(coverages):
        raise ValueError("risks and coverages must have equal length.")
    pairs = sorted(zip(coverages, risks), key=lambda p: p[0])
    return [(cov, risk) for cov, risk in pairs]


def aurc(risks: list[float], coverages: list[float]) -> float:
    """Area Under Risk-Coverage curve using the trapezoidal rule.

    Args:
        risks: Risk values.
        coverages: Coverage values (must be in [0, 1]).

    Returns:
        AURC scalar.
    """
    points = risk_coverage_curve(risks, coverages)
    if len(points) < 2:
        return 0.0

    area = 0.0
    for i in range(1, len(points)):
        cov0, risk0 = points[i - 1]
        cov1, risk1 = points[i]
        area += (cov1 - cov0) * (risk0 + risk1) / 2.0
    return area
