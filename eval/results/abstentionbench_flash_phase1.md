# AbstentionBench Evaluation Report

**Benchmark:** [AbstentionBench](https://huggingface.co/datasets/facebook/AbstentionBench) (Meta, NeurIPS 2025)
**Model:** Gemini 2.5 Flash via Vertex AI
**Examples:** 1,524 across 17 datasets and 5 abstention scenarios
**Temperature:** 0.0
**Date:** 2026-02-23

---

## Methodology

Each example is evaluated twice:

1. **Baseline** — the model receives the question with no system prompt (no AFL protocol)
2. **Treatment** — the model receives the question with the AFL protocol prepended as a system prompt

AbstentionBench provides a ground-truth `should_abstain` boolean label per example, so scoring is binary classification — no LLM judge needed.

A response is classified as an **abstention** if it contains the `FAILURE MODE` template (detected by the AFL scorer). The abstention decision is compared against `should_abstain` to compute precision, recall, and F1.

**Datasets loaded (17 of 20):** alcuna, bbq, big_bench_disambiguate, big_bench_known_unknowns, falseqa, gsm8k_abstain, mediq, mmlu_history_abstain, mmlu_math_abstain, moral_choice, musique, qaqa, qasper, situated_qa, squad2, world_sense, freshqa

**Datasets skipped (3):** gpqa_abstain (gated, requires HuggingFace auth), umwp (missing dependency file), freshqa (empty after load)

**Limit:** 100 examples per dataset

---

## Overall Results

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| **Accuracy** | 58.46% | **71.39%** | +12.93 pp |
| **Abstention Precision** | 0.00% | **77.59%** | — |
| **Abstention Recall** | 0.00% | **43.76%** | +43.76 pp |
| **Abstention F1** | 0.00% | **55.96%** | — |
| **Over-refusal Rate** | 0.00% | 8.98% | +8.98 pp |
| **Abstention Rate** | 0.00% | 23.43% | +23.43 pp |

### Raw Counts

| Count | Baseline | Treatment |
|-------|----------|-----------|
| Total examples | 1,524 | 1,524 |
| Correct | 891 | 1,088 |
| Total abstentions | 0 | 357 |
| Correct abstentions | 0 | 277 |
| False abstentions | 0 | 80 |

**Recovery delta** (treatment recall - baseline recall): **+0.4376**

---

## Per-Scenario Breakdown

### answer_unknown (N=46)

Questions where the answer is genuinely unknown or unknowable.
*Dataset: big_bench_known_unknowns*

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| Accuracy | 50.00% | **93.48%** | +43.48 pp |
| Precision | 0.00% | 88.46% | — |
| Recall | 0.00% | **100.00%** | +100.00 pp |
| F1 | 0.00% | **93.88%** | — |
| Over-refusal | 0.00% | 13.04% | +13.04 pp |
| Abstention rate | 0.00% | 56.52% | +56.52 pp |

AFL's strongest scenario. The model has zero baseline abstention ability on unknown-answer questions — it always guesses. With AFL, it correctly abstains on all 23 should-abstain examples while only over-refusing on 3 of 23 answerable ones.

### underspecified_context (N=1,078)

Questions where the provided context is insufficient for a definitive answer.
*Datasets: alcuna, bbq, big_bench_disambiguate, gsm8k_abstain, mediq, mmlu_history_abstain, mmlu_math_abstain, musique, qasper, squad2, world_sense*

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| Accuracy | 67.07% | **80.15%** | +13.08 pp |
| Precision | 0.00% | 80.00% | — |
| Recall | 0.00% | **52.96%** | +52.96 pp |
| F1 | 0.00% | **63.73%** | — |
| Over-refusal | 0.00% | 6.50% | +6.50 pp |
| Abstention rate | 0.00% | 21.80% | +21.80 pp |

The largest scenario by volume. AFL recovers meaningful abstention (53% recall) while keeping over-refusal low (6.5%). The 80% precision means 4 out of 5 AFL abstentions are correct.

### false_premise (N=200)

Questions built on false or contradictory premises.
*Datasets: falseqa, qaqa*

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| Accuracy | 22.50% | **50.00%** | +27.50 pp |
| Precision | 0.00% | **95.08%** | — |
| Recall | 0.00% | 37.42% | +37.42 pp |
| F1 | 0.00% | **53.70%** | — |
| Over-refusal | 0.00% | 6.67% | +6.67 pp |
| Abstention rate | 0.00% | 30.50% | +30.50 pp |

Extremely high precision (95%) — when AFL flags a false-premise question, it's almost always right. Recall is moderate (37%) because many false premises are subtle enough that the model doesn't detect the contradiction.

### subjective (N=100)

Questions with inherently subjective answers (moral dilemmas, opinion-based).
*Dataset: moral_choice*

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| Accuracy | 0.00% | 8.00% | +8.00 pp |
| Precision | 0.00% | **100.00%** | — |
| Recall | 0.00% | 8.00% | +8.00 pp |
| F1 | 0.00% | 14.81% | — |
| Over-refusal | 0.00% | 0.00% | 0.00 pp |
| Abstention rate | 0.00% | 8.00% | +8.00 pp |

AFL barely triggers here (8% abstention rate), but when it does, it's correct (100% precision, 0% over-refusal). The challenge: subjective questions don't exhibit the structural signals (missing context, unknowable facts) that AFL's heuristic template detects.

### underspecified_intent (N=100)

Questions where the user's intent is ambiguous (e.g., location-dependent answers).
*Dataset: situated_qa*

| Metric | Baseline | Treatment | Delta |
|--------|----------|-----------|-------|
| Accuracy | **100.00%** | 73.00% | -27.00 pp |
| Precision | 0.00% | 0.00% | 0.00 pp |
| Recall | 0.00% | 0.00% | 0.00 pp |
| F1 | 0.00% | 0.00% | 0.00 pp |
| Over-refusal | 0.00% | **27.00%** | +27.00 pp |
| Abstention rate | 0.00% | 27.00% | +27.00 pp |

The only scenario where AFL **hurts**. These are location-dependent questions (e.g., "What is the capital?") where `should_abstain=False` for all 100 examples — every question has a valid answer. The baseline correctly answers all of them. AFL over-refuses on 27, producing pure false abstentions. This is AFL's binary template misapplying to questions that are answerable but context-dependent.

---

## Key Findings

### 1. AFL recovers abstention the baseline entirely lacks

The baseline model **never abstains** — 0% recall across all 1,524 examples. It always produces a direct answer regardless of whether the question is answerable. AFL adds +43.8 percentage points of recall, correctly recovering 277 abstentions that the baseline misses entirely.

### 2. Precision is high where AFL triggers

Overall treatment precision is 77.6% — roughly 3 out of 4 AFL abstentions are correct. In specific scenarios: false_premise hits 95.1% precision, subjective hits 100%, and answer_unknown hits 88.5%. AFL's false-positive rate is low when it does fire.

### 3. Over-refusal is contained

Overall over-refusal is 9.0% — AFL causes false abstentions on about 1 in 11 answerable questions. The exception is underspecified_intent (27%), which is a known weakness.

### 4. AFL's sweet spot is structural uncertainty

The three strongest scenarios (answer_unknown, underspecified_context, false_premise) share a trait: the question has **structural signals** that indicate unanswerability — missing information, contradictory premises, or genuinely unknowable facts. AFL's template-based approach detects these well.

### 5. AFL struggles with nuance-dependent scenarios

Subjective (F1 14.8%) and underspecified_intent (F1 0.0%) require understanding that AFL's binary FAILURE MODE template doesn't capture. Subjective questions need "it depends" rather than a hard stop. Underspecified-intent questions are answerable but context-dependent — AFL's template misreads the ambiguity as a reason to abstain.

---

## Limitations

1. **Single model tested.** Results are for Gemini 2.5 Flash only. Other models may show different baseline and treatment behavior.
2. **100 examples per dataset cap.** Phase 1 uses a subset (1,524 of ~35K+ total). Full-scale results may differ at the margins.
3. **Temperature 0.0 only.** No variance measurement across runs.
4. **3 datasets skipped.** GPQA (gated), UMWP (dependency), and FreshQA (empty) were not evaluated.
5. **No stale-knowledge scenario.** FreshQA (time-sensitive questions) failed to load, so the "stale" scenario is absent.
6. **Binary scoring only.** AbstentionBench labels are boolean. Partial abstention (hedging, caveats) is not captured — either the model produces FAILURE MODE or it doesn't.

---

## Reproduction

```bash
python3 -m eval.benchmarks.cli abstentionbench \
  --vertex --project PROJECT --location global \
  --model google/gemini-2.5-flash \
  --limit 100 \
  --temperature 0.0 \
  --output eval/results/abstentionbench_flash_phase1.md \
  --output-json eval/results/abstentionbench_flash_phase1.json
```

Requires: `pip install datasets huggingface_hub openai google-auth`

Raw JSON data: [`abstentionbench_flash_phase1.json`](abstentionbench_flash_phase1.json)
