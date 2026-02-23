# Benchmark Report: AbstentionBench

**Model:** google/gemini-2.5-flash  
**Examples:** 1524  
**Generated:** 2026-02-23 08:08 UTC

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| baseline.accuracy | 0.5846 |
| baseline.precision | 0.0000 |
| baseline.recall | 0.0000 |
| baseline.f1 | 0.0000 |
| baseline.over_refusal_rate | 0.0000 |
| baseline.abstention_rate | 0.0000 |
| baseline.total | 1524 |
| baseline.correct | 891 |
| baseline.total_abstentions | 0 |
| baseline.correct_abstentions | 0 |
| baseline.false_abstentions | 0 |
| treatment.accuracy | 0.7139 |
| treatment.precision | 0.7759 |
| treatment.recall | 0.4376 |
| treatment.f1 | 0.5596 |
| treatment.over_refusal_rate | 0.0898 |
| treatment.abstention_rate | 0.2343 |
| treatment.total | 1524 |
| treatment.correct | 1088 |
| treatment.total_abstentions | 357 |
| treatment.correct_abstentions | 277 |
| treatment.false_abstentions | 80 |
| per_scenario.answer_unknown | {'baseline': {'accuracy': 0.5, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.0, 'abstention_rate': 0.0, 'total': 46, 'correct': 23, 'total_abstentions': 0, 'correct_abstentions': 0, 'false_abstentions': 0}, 'treatment': {'accuracy': 0.9348, 'precision': 0.8846, 'recall': 1.0, 'f1': 0.9388, 'over_refusal_rate': 0.1304, 'abstention_rate': 0.5652, 'total': 46, 'correct': 43, 'total_abstentions': 26, 'correct_abstentions': 23, 'false_abstentions': 3}} |
| per_scenario.false_premise | {'baseline': {'accuracy': 0.225, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.0, 'abstention_rate': 0.0, 'total': 200, 'correct': 45, 'total_abstentions': 0, 'correct_abstentions': 0, 'false_abstentions': 0}, 'treatment': {'accuracy': 0.5, 'precision': 0.9508, 'recall': 0.3742, 'f1': 0.537, 'over_refusal_rate': 0.0667, 'abstention_rate': 0.305, 'total': 200, 'correct': 100, 'total_abstentions': 61, 'correct_abstentions': 58, 'false_abstentions': 3}} |
| per_scenario.subjective | {'baseline': {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.0, 'abstention_rate': 0.0, 'total': 100, 'correct': 0, 'total_abstentions': 0, 'correct_abstentions': 0, 'false_abstentions': 0}, 'treatment': {'accuracy': 0.08, 'precision': 1.0, 'recall': 0.08, 'f1': 0.1481, 'over_refusal_rate': 0.0, 'abstention_rate': 0.08, 'total': 100, 'correct': 8, 'total_abstentions': 8, 'correct_abstentions': 8, 'false_abstentions': 0}} |
| per_scenario.underspecified_context | {'baseline': {'accuracy': 0.6707, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.0, 'abstention_rate': 0.0, 'total': 1078, 'correct': 723, 'total_abstentions': 0, 'correct_abstentions': 0, 'false_abstentions': 0}, 'treatment': {'accuracy': 0.8015, 'precision': 0.8, 'recall': 0.5296, 'f1': 0.6373, 'over_refusal_rate': 0.065, 'abstention_rate': 0.218, 'total': 1078, 'correct': 864, 'total_abstentions': 235, 'correct_abstentions': 188, 'false_abstentions': 47}} |
| per_scenario.underspecified_intent | {'baseline': {'accuracy': 1.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.0, 'abstention_rate': 0.0, 'total': 100, 'correct': 100, 'total_abstentions': 0, 'correct_abstentions': 0, 'false_abstentions': 0}, 'treatment': {'accuracy': 0.73, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'over_refusal_rate': 0.27, 'abstention_rate': 0.27, 'total': 100, 'correct': 73, 'total_abstentions': 27, 'correct_abstentions': 0, 'false_abstentions': 27}} |
| recovery_delta | 0.4376 |

## Statistical Tests

- Baseline score: 0.000 (95% CI [0.000, 0.000])
- Treatment score: 0.000 (95% CI [0.000, 0.000])
- McNemar's test (baseline vs treatment): p=1.0000, n_discordant=0

## Raw Counts

- Total examples: 1524
- AFL abstentions (treatment): 357

---

> **Disclaimer:** These results measure AFL protocol instruction-following effectiveness. Runtime hook enforcement is validated separately.