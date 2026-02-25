"""AbstentionBench adapter for AFL evaluation.

AbstentionBench (Meta, NeurIPS 2025) tests whether a model abstains when it
should. 35K+ queries across 20 datasets and 6 scenarios. Ground-truth
``should_abstain`` labels eliminate the need for LLM judges — scoring is
binary classification (precision / recall / F1).

HuggingFace dataset: facebook/AbstentionBench
"""

from __future__ import annotations

import glob
import importlib.util
import json
import logging
import os
import sys
from typing import Any

from eval.benchmarks._framework.types import (
    BenchmarkExample,
    ModelResponse,
    ScoredExample,
)

logger = logging.getLogger(__name__)

# Scenario → dataset split mapping (from AbstentionBench source).
SCENARIO_SPLITS: dict[str, list[str]] = {
    "underspecified_context": [
        "alcuna",
        "bbq",
        "big_bench_disambiguate",
        "mediq",
        "musique",
        "qasper",
        "squad2",
        "world_sense",
        "gpqa_abstain",
        "gsm8k_abstain",
        "mmlu_math_abstain",
        "mmlu_history_abstain",
        "umwp",
    ],
    "answer_unknown": [
        "big_bench_known_unknowns",
    ],
    "false_premise": [
        "falseqa",
        "qaqa",
    ],
    "subjective": [
        "moral_choice",
    ],
    "underspecified_intent": [
        "situated_qa",
    ],
    "stale": [
        "freshqa",
    ],
}

# Reverse lookup: dataset → scenario.
_DATASET_TO_SCENARIO: dict[str, str] = {}
for _scenario, _datasets in SCENARIO_SPLITS.items():
    for _ds in _datasets:
        _DATASET_TO_SCENARIO[_ds] = _scenario


def _scenario_for_dataset(name: str) -> str:
    return _DATASET_TO_SCENARIO.get(name, "unknown")


def _get_abstentionbench_data_module():
    """Import the cached AbstentionBench ``data.py`` module.

    The first ``load_dataset("facebook/AbstentionBench", ...)`` call
    downloads and caches the dataset script.  This function locates
    that cached ``data.py`` and imports it so we can instantiate
    individual dataset classes without the eager-init main script.
    """
    pattern = (
        "~/.cache/huggingface/modules/datasets_modules/"
        "datasets/facebook--AbstentionBench/*/data.py"
    )
    hits = glob.glob(os.path.expanduser(pattern))
    if not hits:
        return None

    spec = importlib.util.spec_from_file_location("_abstentionbench_data", hits[0])
    if spec is None or spec.loader is None:
        return None

    mod = importlib.util.module_from_spec(spec)
    sys.modules["_abstentionbench_data"] = mod
    spec.loader.exec_module(mod)
    return mod


class AbstentionBenchAdapter:
    """Loads AbstentionBench from HuggingFace and scores abstention behaviour."""

    def __init__(
        self,
        scenarios: list[str] | None = None,
        **client_kwargs: Any,
    ) -> None:
        self.scenarios = scenarios
        self.client_kwargs = client_kwargs

    # ------------------------------------------------------------------
    # BenchmarkAdapter protocol
    # ------------------------------------------------------------------

    def load_examples(
        self,
        split: str = "all",
        limit: int | None = None,
        fast_subset: bool = False,
    ) -> list[BenchmarkExample]:
        """Load examples from AbstentionBench.

        Loads each dataset individually via AbstentionBench's ``data.py``
        classes, bypassing the main script's eager init (which would fail on
        gated datasets like GPQA unless authenticated).

        Args:
            split: Dataset config name (e.g. ``"bbq"``) or ``"all"``.
            limit: Cap examples per config.  Use for smoke tests.
            fast_subset: If True, use AbstentionBench's own fast-subset
                         indices (100 per dataset).
        """
        examples: list[BenchmarkExample] = []

        if split == "all":
            config_names = list(_DATASET_TO_SCENARIO.keys())
        else:
            config_names = [split]

        # Filter by scenario if requested.
        if self.scenarios:
            allowed: set[str] = set()
            for s in self.scenarios:
                allowed.update(SCENARIO_SPLITS.get(s, []))
            config_names = [c for c in config_names if c in allowed]

        # Optionally load fast-subset indices.
        subset_indices: dict[str, list[int]] | None = None
        if fast_subset:
            subset_indices = self._load_fast_subset_indices()

        for cfg in config_names:
            ds = self._load_single_dataset(cfg)
            if ds is None:
                continue

            indices: range | list[int]
            if subset_indices is not None and cfg in subset_indices:
                indices = subset_indices[cfg]
            else:
                indices = range(len(ds))

            if limit is not None:
                indices = list(indices)[:limit]

            for idx in indices:
                row = ds[int(idx)]
                ex = self._row_to_example(row, cfg, idx)
                examples.append(ex)

        return examples

    def format_prompt(
        self,
        example: BenchmarkExample,
        with_protocol: bool = False,
    ) -> str:
        return example.prompt

    def score_response(
        self,
        example: BenchmarkExample,
        response: ModelResponse,
    ) -> dict[str, Any]:
        should_abstain: bool = example.ground_truth
        abstained: bool = response.is_abstention
        correct = abstained == should_abstain

        return {
            "abstained": abstained,
            "should_abstain": should_abstain,
            "correct": correct,
            "afl_status": response.afl_status,
        }

    def aggregate(self, scored: list[ScoredExample]) -> dict[str, Any]:
        """Compute precision, recall, F1, and per-scenario breakdowns.

        Dynamically discovers arms from the scores dicts (baseline, treatment,
        and optionally naive).
        """
        # Discover which arms are present.
        arms: list[str] = []
        for name in ("baseline", "naive", "treatment"):
            if any(name in s.scores for s in scored):
                arms.append(name)

        metrics: dict[str, Any] = {}

        for arm in arms:
            arm_scores = [s.scores.get(arm, {}) for s in scored]
            metrics[arm] = self._compute_metrics(arm_scores)

        # Per-scenario breakdown.
        scenarios: dict[str, dict[str, list[dict]]] = {}
        for s in scored:
            scenario = s.example.metadata.get("scenario", "unknown")
            scenarios.setdefault(scenario, {a: [] for a in arms})
            for arm in arms:
                if arm in s.scores:
                    scenarios[scenario][arm].append(s.scores[arm])

        per_scenario: dict[str, dict] = {}
        for scenario, scenario_arms in sorted(scenarios.items()):
            per_scenario[scenario] = {}
            for arm in arms:
                per_scenario[scenario][arm] = self._compute_metrics(
                    scenario_arms.get(arm, [])
                )

        metrics["per_scenario"] = per_scenario

        # Recovery delta: treatment recall − baseline recall.
        b_recall = metrics.get("baseline", {}).get("recall", 0.0)
        t_recall = metrics.get("treatment", {}).get("recall", 0.0)
        metrics["recovery_delta"] = round(t_recall - b_recall, 4)

        return metrics

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _load_single_dataset(config_name: str):
        """Load one AbstentionBench dataset directly via its data.py class.

        This bypasses the main ``AbstentionBench.py`` script which eagerly
        initialises ALL datasets (including gated ones like GPQA).
        """
        # Map config name → class name in data.py
        _CONFIG_TO_CLASS: dict[str, str] = {
            "alcuna": "ALCUNADataset",
            "bbq": "BBQDataset",
            "big_bench_disambiguate": "BigBenchDisambiguateDataset",
            "big_bench_known_unknowns": "BigBenchKnownUnknownsDataset",
            "coconot": "CoCoNotDataset",
            "falseqa": "FalseQADataset",
            "gpqa_abstain": "GPQA",
            "gsm8k_abstain": "GSM8K",
            "known_unknown_questions": "KUQDataset",
            "mediq": "MediQDataset",
            "mmlu_history_abstain": "MMLUHistory",
            "mmlu_math_abstain": "MMLUMath",
            "moral_choice": "MoralChoiceDataset",
            "musique": "MusiqueDataset",
            "qaqa": "QAQADataset",
            "qasper": "QASPERDataset",
            "situated_qa": "SituatedQAGeoDataset",
            "squad2": "Squad2Dataset",
            "umwp": "UMWP",
            "world_sense": "WorldSenseDataset",
        }

        class_name = _CONFIG_TO_CLASS.get(config_name)
        if class_name is None:
            logger.warning("Unknown config %r, skipping", config_name)
            return None

        # Import from the cached AbstentionBench data.py module.
        data_mod = _get_abstentionbench_data_module()
        if data_mod is None:
            logger.warning(
                "AbstentionBench data module not found; "
                "run load_dataset('facebook/AbstentionBench'"
                ", trust_remote_code=True) to cache it."
            )
            return None

        cls = getattr(data_mod, class_name, None)
        if cls is None:
            logger.warning(
                "Class %s not found in data module, skipping %s",
                class_name,
                config_name,
            )
            return None

        try:
            obj = cls()
            return obj.to_hf_dataset(split=config_name)
        except Exception as exc:
            logger.warning("Failed to load %s: %s — skipping", config_name, exc)
            return None

    @staticmethod
    def _row_to_example(
        row: dict[str, Any],
        dataset_name: str,
        index: int,
    ) -> BenchmarkExample:
        question = row.get("question") or row.get("prompt") or ""
        should_abstain = bool(row.get("should_abstain", False))

        ref_answers = row.get("reference_answers", [])
        if isinstance(ref_answers, str):
            try:
                ref_answers = json.loads(ref_answers)
            except (json.JSONDecodeError, TypeError):
                ref_answers = [ref_answers] if ref_answers else []

        metadata_raw = row.get("metadata_json") or row.get("metadata") or "{}"
        if isinstance(metadata_raw, str):
            try:
                extra_meta = json.loads(metadata_raw)
            except (json.JSONDecodeError, TypeError):
                extra_meta = {}
        elif isinstance(metadata_raw, dict):
            extra_meta = metadata_raw
        else:
            extra_meta = {}

        return BenchmarkExample(
            id=f"{dataset_name}_{index}",
            prompt=question,
            ground_truth=should_abstain,
            metadata={
                "scenario": _scenario_for_dataset(dataset_name),
                "dataset_name": dataset_name,
                "reference_answers": ref_answers,
                **extra_meta,
            },
        )

    @staticmethod
    def _compute_metrics(scores: list[dict[str, Any]]) -> dict[str, Any]:
        if not scores:
            return {}

        total = len(scores)
        correct = sum(1 for s in scores if s.get("correct", False))
        total_abstentions = sum(1 for s in scores if s.get("abstained", False))
        correct_abstentions = sum(
            1 for s in scores if s.get("abstained") and s.get("should_abstain")
        )
        false_abstentions = sum(
            1 for s in scores if s.get("abstained") and not s.get("should_abstain")
        )
        should_have_abstained = sum(1 for s in scores if s.get("should_abstain", False))
        total_answerable = total - should_have_abstained

        precision = (
            correct_abstentions / total_abstentions if total_abstentions > 0 else 0.0
        )
        recall = (
            correct_abstentions / should_have_abstained
            if should_have_abstained > 0
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        over_refusal_rate = (
            false_abstentions / total_answerable if total_answerable > 0 else 0.0
        )

        return {
            "accuracy": round(correct / total, 4) if total else 0.0,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "over_refusal_rate": round(over_refusal_rate, 4),
            "abstention_rate": round(total_abstentions / total, 4) if total else 0.0,
            "total": total,
            "correct": correct,
            "total_abstentions": total_abstentions,
            "correct_abstentions": correct_abstentions,
            "false_abstentions": false_abstentions,
        }

    @staticmethod
    def _load_fast_subset_indices() -> dict[str, list[int]]:
        """Load AbstentionBench subsampling indices from HuggingFace.

        The official ``subsampling-indices.json`` uses class names as keys
        (e.g. ``ALCUNADataset``).  We map them back to config names so the
        caller can look up indices by config.
        """
        # Class name → config name mapping (reverse of _CONFIG_TO_CLASS).
        _CLASS_TO_CONFIG: dict[str, str] = {
            "ALCUNADataset": "alcuna",
            "BBQDataset": "bbq",
            "KUQDataset": "known_unknown_questions",
            "Squad2Dataset": "squad2",
        }

        try:
            from huggingface_hub import hf_hub_download  # noqa: PLC0415

            path = hf_hub_download(
                repo_id="facebook/AbstentionBench",
                filename="subsampling-indices.json",
                repo_type="dataset",
            )
            with open(path) as f:
                raw: dict[str, list[int]] = json.load(f)

            # Re-key from class names to config names.
            result: dict[str, list[int]] = {}
            for class_name, indices in raw.items():
                cfg = _CLASS_TO_CONFIG.get(class_name)
                if cfg:
                    result[cfg] = indices
            return result
        except Exception:
            return {}
