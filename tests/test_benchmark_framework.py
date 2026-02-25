"""Unit tests for AFL benchmark evaluation framework.

All tests run without API keys — only local logic is exercised.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestTypes(unittest.TestCase):
    """Test shared data types."""

    def test_benchmark_example_creation(self) -> None:
        from eval.benchmarks._framework.types import BenchmarkExample

        ex = BenchmarkExample(id="q1", prompt="What is 2+2?", ground_truth="4")
        self.assertEqual(ex.id, "q1")
        self.assertEqual(ex.prompt, "What is 2+2?")
        self.assertEqual(ex.ground_truth, "4")
        self.assertEqual(ex.metadata, {})

    def test_model_response_defaults(self) -> None:
        from eval.benchmarks._framework.types import ModelResponse

        resp = ModelResponse(text="hello")
        self.assertEqual(resp.text, "hello")
        self.assertFalse(resp.is_abstention)
        self.assertIsNone(resp.afl_status)
        self.assertEqual(resp.metadata, {})

    def test_scored_example(self) -> None:
        from eval.benchmarks._framework.types import (
            BenchmarkExample,
            ModelResponse,
            ScoredExample,
        )

        ex = BenchmarkExample(id="1", prompt="p", ground_truth="g")
        base = ModelResponse(text="base answer")
        treat = ModelResponse(text="FAILURE MODE", is_abstention=True)
        scored = ScoredExample(
            example=ex,
            baseline_response=base,
            treatment_response=treat,
            scores={"correct": True},
        )
        self.assertEqual(scored.scores["correct"], True)

    def test_benchmark_result(self) -> None:
        from eval.benchmarks._framework.types import BenchmarkResult

        result = BenchmarkResult(
            benchmark_name="TestBench",
            model="test-model",
            num_examples=5,
            metrics={"accuracy": 0.8},
        )
        self.assertEqual(result.benchmark_name, "TestBench")
        self.assertEqual(result.num_examples, 5)
        self.assertEqual(result.scored_examples, [])


class TestScorer(unittest.TestCase):
    """Test AFL template parsing."""

    def test_parse_compliant_response(self) -> None:
        from eval.benchmarks._framework.scorer import parse_afl_response

        text = (
            "FAILURE MODE\n\n"
            "Status: CANNOT_VERIFY\n\n"
            "Blocked because:\n- Cannot predict future\n\n"
            "To proceed I need:\n- Clarified question\n\n"
            "Safe next actions (I can do now):\n1) Explain limitations"
        )
        is_abstention, status, fields = parse_afl_response(text)
        self.assertTrue(is_abstention)
        self.assertEqual(status, "CANNOT_VERIFY")
        self.assertIn("blocked_because", fields)

    def test_parse_non_compliant_response(self) -> None:
        from eval.benchmarks._framework.scorer import parse_afl_response

        text = "The answer is 42."
        is_abstention, status, fields = parse_afl_response(text)
        self.assertFalse(is_abstention)
        self.assertIsNone(status)
        self.assertEqual(fields, {})

    def test_parse_needs_info_status(self) -> None:
        from eval.benchmarks._framework.scorer import parse_afl_response

        text = (
            "FAILURE MODE\n\n"
            "Status: NEEDS_INFO\n\n"
            "Blocked because:\n- Missing context\n\n"
            "To proceed I need:\n- Logs\n\n"
            "Safe next actions (I can do now):\n1) Ask for repro steps"
        )
        is_abstention, status, _ = parse_afl_response(text)
        self.assertTrue(is_abstention)
        self.assertEqual(status, "NEEDS_INFO")


class TestStats(unittest.TestCase):
    """Test statistical utilities."""

    def test_bootstrap_ci(self) -> None:
        from eval.benchmarks._framework.stats import bootstrap_ci

        mean, lower, upper = bootstrap_ci([1.0, 1.0, 1.0, 0.0, 0.0])
        self.assertAlmostEqual(mean, 0.6)
        self.assertGreaterEqual(lower, 0.0)
        self.assertLessEqual(upper, 1.0)
        self.assertLessEqual(lower, mean)
        self.assertLessEqual(mean, upper)

    def test_bootstrap_ci_perfect(self) -> None:
        from eval.benchmarks._framework.stats import bootstrap_ci

        mean, lower, upper = bootstrap_ci([1.0, 1.0, 1.0])
        self.assertAlmostEqual(mean, 1.0)
        self.assertAlmostEqual(lower, 1.0)
        self.assertAlmostEqual(upper, 1.0)

    def test_mcnemar(self) -> None:
        from eval.benchmarks._framework.stats import mcnemar_test

        result = mcnemar_test(
            [True, True, False, False],
            [True, False, True, False],
        )
        self.assertIn("p_value", result)
        self.assertIn("statistic", result)
        self.assertIn("n_discordant", result)
        self.assertGreaterEqual(result["p_value"], 0.0)
        self.assertLessEqual(result["p_value"], 1.0)

    def test_aurc(self) -> None:
        from eval.benchmarks._framework.stats import aurc

        score = aurc([0.1, 0.2, 0.3], [0.3, 0.6, 1.0])
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestProtocol(unittest.TestCase):
    """Test protocol loading and prompt building."""

    def test_load_protocol(self) -> None:
        from eval.benchmarks._framework.protocol import load_afl_protocol

        protocol = load_afl_protocol()
        self.assertIn("FAILURE MODE", protocol)
        self.assertIn("Status:", protocol)

    def test_build_system_prompt_with_afl(self) -> None:
        from eval.benchmarks._framework.protocol import build_system_prompt

        prompt = build_system_prompt("You are helpful.", with_afl=True)
        self.assertIn("FAILURE MODE", prompt)
        self.assertIn("You are helpful.", prompt)

    def test_build_system_prompt_without_afl(self) -> None:
        from eval.benchmarks._framework.protocol import build_system_prompt

        prompt = build_system_prompt("You are helpful.", with_afl=False)
        self.assertNotIn("FAILURE MODE", prompt)
        self.assertIn("You are helpful.", prompt)


class TestRuntimeFidelity(unittest.TestCase):
    """Verify AFL hooks detect/enforce template compliance."""

    def test_runtime_fidelity(self) -> None:
        from hooks.afl_lib import is_failure_mode_message_compliant, load_policy

        compliant = (
            "FAILURE MODE\n\n"
            "Status: CANNOT_VERIFY\n\n"
            "Blocked because:\n- test\n\n"
            "To proceed I need:\n- info\n\n"
            "Safe next actions (I can do now):\n1) wait"
        )
        non_compliant = "I think the answer is 42."

        policy = load_policy(Path("."))
        self.assertTrue(is_failure_mode_message_compliant(compliant, policy))
        self.assertFalse(is_failure_mode_message_compliant(non_compliant, policy))


class TestReport(unittest.TestCase):
    """Test report generation."""

    def test_generate_report(self) -> None:
        from eval.benchmarks._framework.report import generate_report
        from eval.benchmarks._framework.types import BenchmarkResult

        result = BenchmarkResult(
            benchmark_name="Test",
            model="test-model",
            num_examples=10,
            metrics={"accuracy": 0.9},
        )
        report = generate_report(result)
        self.assertIn("Test", report)
        self.assertIn("test-model", report)
        self.assertIn("instruction-following effectiveness", report)


class TestClient(unittest.TestCase):
    """Test client factory."""

    def test_default_client(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            from importlib import reload

            import eval.benchmarks._framework.client as client_mod

            reload(client_mod)
            client = client_mod.create_client(api_key="test-key")
            mock_openai.OpenAI.assert_called_once_with(
                api_key="test-key", base_url=None
            )
            self.assertIs(client, mock_client)

    def test_custom_base_url(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            from importlib import reload

            import eval.benchmarks._framework.client as client_mod

            reload(client_mod)
            client = client_mod.create_client(
                api_key="test-key", base_url="https://example.com/v1"
            )
            mock_openai.OpenAI.assert_called_once_with(
                api_key="test-key", base_url="https://example.com/v1"
            )
            self.assertIs(client, mock_client)

    def test_vertex_missing_google_auth(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_openai = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "openai": mock_openai,
                "google": None,
                "google.auth": None,
                "google.auth.transport": None,
                "google.auth.transport.requests": None,
            },
        ):
            from importlib import reload

            import eval.benchmarks._framework.client as client_mod

            reload(client_mod)
            with self.assertRaises(ImportError) as ctx:
                client_mod.create_client(vertex=True, project="my-project")
            self.assertIn("google-auth", str(ctx.exception))

    def test_vertex_missing_project(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_openai = MagicMock()
        mock_google_auth = MagicMock()
        mock_google_auth.default.return_value = (MagicMock(), "project-id")
        mock_transport = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "openai": mock_openai,
                    "google": MagicMock(),
                    "google.auth": mock_google_auth,
                    "google.auth.transport": mock_transport,
                    "google.auth.transport.requests": mock_transport.requests,
                },
            ),
            patch.dict("os.environ", {}, clear=True),
        ):
            from importlib import reload

            import eval.benchmarks._framework.client as client_mod

            reload(client_mod)
            with self.assertRaises(ValueError) as ctx:
                client_mod.create_client(vertex=True)
            self.assertIn("project", str(ctx.exception).lower())


class TestAbstentionBench(unittest.TestCase):
    """Test AbstentionBench adapter logic (no network calls)."""

    def _make_adapter(self):
        from eval.benchmarks.abstentionbench.adapter import AbstentionBenchAdapter

        return AbstentionBenchAdapter()

    def test_adapter_load_mock(self) -> None:
        """Mock dataset loading and verify BenchmarkExample mapping."""
        from unittest.mock import MagicMock, patch

        from eval.benchmarks.abstentionbench.adapter import (
            AbstentionBenchAdapter,
        )

        fake_rows = [
            {
                "question": "What color is the sky on Mars?",
                "reference_answers": '["reddish"]',
                "should_abstain": False,
                "metadata_json": '{"source": "test"}',
            },
            {
                "question": "What will happen tomorrow?",
                "reference_answers": "[]",
                "should_abstain": True,
                "metadata_json": "{}",
            },
        ]

        fake_dataset = MagicMock()
        fake_dataset.__len__ = lambda self: len(fake_rows)
        fake_dataset.__getitem__ = lambda self, idx: fake_rows[idx]

        with patch.object(
            AbstentionBenchAdapter,
            "_load_single_dataset",
            return_value=fake_dataset,
        ):
            adapter = AbstentionBenchAdapter()
            examples = adapter.load_examples(split="bbq", limit=10)

        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].id, "bbq_0")
        self.assertEqual(examples[0].prompt, "What color is the sky on Mars?")
        self.assertFalse(examples[0].ground_truth)
        self.assertEqual(examples[1].id, "bbq_1")
        self.assertTrue(examples[1].ground_truth)

    def test_score_correct_abstention(self) -> None:
        """Model abstains when should_abstain=True → correct."""
        from eval.benchmarks._framework.types import BenchmarkExample, ModelResponse

        adapter = self._make_adapter()
        ex = BenchmarkExample(
            id="t1",
            prompt="p",
            ground_truth=True,
            metadata={"scenario": "underspecified_context"},
        )
        resp = ModelResponse(
            text="FAILURE MODE\n...", is_abstention=True, afl_status="CANNOT_VERIFY"
        )
        result = adapter.score_response(ex, resp)
        self.assertTrue(result["correct"])
        self.assertTrue(result["abstained"])
        self.assertTrue(result["should_abstain"])

    def test_score_false_abstention(self) -> None:
        """Model abstains when should_abstain=False → over-refusal."""
        from eval.benchmarks._framework.types import BenchmarkExample, ModelResponse

        adapter = self._make_adapter()
        ex = BenchmarkExample(
            id="t2",
            prompt="p",
            ground_truth=False,
            metadata={"scenario": "underspecified_context"},
        )
        resp = ModelResponse(text="FAILURE MODE\n...", is_abstention=True)
        result = adapter.score_response(ex, resp)
        self.assertFalse(result["correct"])
        self.assertTrue(result["abstained"])
        self.assertFalse(result["should_abstain"])

    def test_score_missed_abstention(self) -> None:
        """Model answers when should_abstain=True → missed."""
        from eval.benchmarks._framework.types import BenchmarkExample, ModelResponse

        adapter = self._make_adapter()
        ex = BenchmarkExample(
            id="t3",
            prompt="p",
            ground_truth=True,
            metadata={"scenario": "false_premise"},
        )
        resp = ModelResponse(text="The answer is 42.")
        result = adapter.score_response(ex, resp)
        self.assertFalse(result["correct"])
        self.assertFalse(result["abstained"])
        self.assertTrue(result["should_abstain"])

    def test_aggregate_metrics(self) -> None:
        """Verify precision/recall/F1 computation."""
        from eval.benchmarks._framework.types import (
            BenchmarkExample,
            ModelResponse,
            ScoredExample,
        )

        adapter = self._make_adapter()

        # Build 4 scored examples covering all quadrants:
        # 1. should_abstain=True,  abstained=True  → correct abstention
        # 2. should_abstain=True,  abstained=False → missed
        # 3. should_abstain=False, abstained=True  → over-refusal
        # 4. should_abstain=False, abstained=False → correct answer
        cases = [
            (True, True),  # correct abstention
            (True, False),  # missed
            (False, True),  # over-refusal
            (False, False),  # correct answer
        ]

        scored = []
        for i, (should, did) in enumerate(cases):
            ex = BenchmarkExample(
                id=f"a{i}",
                prompt="q",
                ground_truth=should,
                metadata={"scenario": "underspecified_context"},
            )
            resp = ModelResponse(
                text="FAILURE MODE" if did else "answer",
                is_abstention=did,
            )
            score = adapter.score_response(ex, resp)
            se = ScoredExample(
                example=ex,
                baseline_response=resp,
                treatment_response=resp,
                scores={"baseline": score, "treatment": score},
            )
            scored.append(se)

        metrics = adapter.aggregate(scored)

        # Treatment arm: 1 correct abstention out of 2 total abstentions → precision=0.5
        # 1 correct abstention out of 2 should_abstain → recall=0.5
        # F1 = 2 * 0.5 * 0.5 / (0.5 + 0.5) = 0.5
        # Over-refusal: 1 false abstention out of 2 answerable → 0.5
        t = metrics["treatment"]
        self.assertAlmostEqual(t["precision"], 0.5)
        self.assertAlmostEqual(t["recall"], 0.5)
        self.assertAlmostEqual(t["f1"], 0.5)
        self.assertAlmostEqual(t["over_refusal_rate"], 0.5)
        self.assertEqual(t["total"], 4)
        self.assertEqual(t["correct"], 2)

        # Recovery delta should be 0 since baseline == treatment here.
        self.assertAlmostEqual(metrics["recovery_delta"], 0.0)

        # Per-scenario should have exactly one entry.
        self.assertIn("underspecified_context", metrics["per_scenario"])

    def test_aggregate_with_naive_arm(self) -> None:
        """Verify aggregate handles a third 'naive' arm."""
        from eval.benchmarks._framework.types import (
            BenchmarkExample,
            ModelResponse,
            ScoredExample,
        )

        adapter = self._make_adapter()

        # Two examples: one should abstain, one should answer.
        cases = [(True, True, False), (False, False, True)]
        scored = []
        for i, (should, treatment_did, naive_did) in enumerate(cases):
            ex = BenchmarkExample(
                id=f"n{i}",
                prompt="q",
                ground_truth=should,
                metadata={"scenario": "answer_unknown"},
            )
            base_resp = ModelResponse(text="answer", is_abstention=False)
            treat_resp = ModelResponse(
                text="FAILURE MODE" if treatment_did else "answer",
                is_abstention=treatment_did,
            )
            naive_resp = ModelResponse(
                text="I don't know" if naive_did else "answer",
                is_abstention=naive_did,
            )
            base_score = adapter.score_response(ex, base_resp)
            treat_score = adapter.score_response(ex, treat_resp)
            naive_score = adapter.score_response(ex, naive_resp)

            se = ScoredExample(
                example=ex,
                baseline_response=base_resp,
                treatment_response=treat_resp,
                scores={
                    "baseline": base_score,
                    "treatment": treat_score,
                    "naive": naive_score,
                },
            )
            scored.append(se)

        metrics = adapter.aggregate(scored)

        self.assertIn("naive", metrics)
        self.assertIn("naive", metrics["per_scenario"]["answer_unknown"])
        # Naive arm: abstained on case 1 (should_answer) = false abstention.
        self.assertEqual(metrics["naive"]["false_abstentions"], 1)


class TestReportScoreExtraction(unittest.TestCase):
    """Verify report.py correctly extracts scores from AbstentionBench format."""

    def test_report_uses_correct_key(self) -> None:
        from eval.benchmarks._framework.report import generate_report
        from eval.benchmarks._framework.types import (
            BenchmarkExample,
            BenchmarkResult,
            ModelResponse,
            ScoredExample,
        )

        ex = BenchmarkExample(id="r1", prompt="p", ground_truth=True, metadata={})
        base = ModelResponse(text="answer")
        treat = ModelResponse(text="FAILURE MODE", is_abstention=True)
        se = ScoredExample(
            example=ex,
            baseline_response=base,
            treatment_response=treat,
            scores={
                "baseline": {
                    "correct": False,
                    "abstained": False,
                    "should_abstain": True,
                },
                "treatment": {
                    "correct": True,
                    "abstained": True,
                    "should_abstain": True,
                },
            },
        )
        result = BenchmarkResult(
            benchmark_name="Test",
            model="test-model",
            num_examples=1,
            metrics={"accuracy": 0.5},
            scored_examples=[se],
        )
        report = generate_report(result)
        # With the fix, baseline should be 0.0 and treatment 1.0
        self.assertIn("Baseline accuracy: 0.000", report)
        self.assertIn("Treatment accuracy: 1.000", report)
        # McNemar should show n_discordant=1 (not 0 from all-zeros)
        self.assertIn("n_discordant=1", report)


if __name__ == "__main__":
    unittest.main()
