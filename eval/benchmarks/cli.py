"""Unified CLI for AFL benchmark evaluation.

Usage:
    python -m eval.benchmarks.cli <benchmark> [options]
"""

from __future__ import annotations

import importlib
import sys

_BENCHMARKS = {
    "abstentionbench": "eval.benchmarks.abstentionbench.run",
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m eval.benchmarks.cli <benchmark> [options]")
        print()
        print("Benchmarks:")
        for name in sorted(_BENCHMARKS):
            print(f"  {name}")
        print()
        sys.exit(0)

    benchmark = sys.argv[1]
    # Strip the benchmark name so the sub-command's argparse sees only its flags.
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if benchmark in _BENCHMARKS:
        mod = importlib.import_module(_BENCHMARKS[benchmark])
        mod.main()
    else:
        print(f"Unknown benchmark: {benchmark}")
        print(f"Available: {', '.join(sorted(_BENCHMARKS))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
