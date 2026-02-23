"""Shared data types for the AFL benchmark evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class BenchmarkExample:
    """A single benchmark question/example."""

    id: str
    prompt: str
    ground_truth: Any
    metadata: dict = field(default_factory=dict)


@dataclass
class ModelResponse:
    """A model's response to a benchmark example."""

    text: str
    is_abstention: bool = False
    afl_status: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredExample:
    """A benchmark example with both baseline and treatment responses scored."""

    example: BenchmarkExample
    baseline_response: ModelResponse
    treatment_response: ModelResponse
    scores: dict = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Aggregate results for a benchmark run."""

    benchmark_name: str
    model: str
    num_examples: int
    metrics: dict = field(default_factory=dict)
    scored_examples: list[ScoredExample] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class BenchmarkAdapter(Protocol):
    """Protocol that all benchmark adapters must implement."""

    def load_examples(
        self, split: str = "validation", limit: int | None = None
    ) -> list[BenchmarkExample]: ...

    def format_prompt(
        self, example: BenchmarkExample, with_protocol: bool = False
    ) -> str: ...

    def score_response(
        self, example: BenchmarkExample, response: ModelResponse
    ) -> dict: ...

    def aggregate(self, scored: list[ScoredExample]) -> dict: ...
