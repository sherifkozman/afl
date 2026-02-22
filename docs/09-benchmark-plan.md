# AFL Benchmark Integration Plan

## Overview

This plan evaluates AFL against three established benchmarks to strengthen the evidence base beyond the current 7-prompt custom suite. Each benchmark tests a different facet of AFL's value proposition.

| Benchmark | What it tests for AFL | Novelty | Effort |
|-----------|----------------------|---------|--------|
| **TruthfulQA** | Selective abstention on trick questions | High — no prior structured-template work | Low |
| **HaluEval** | Prevention vs. detection of hallucination | High — no prior abstention work on HaluEval | Medium |
| **SWE-bench** | Honest failure in agentic coding tasks | Very high — no one measures abstention on SWE-bench | High |

Priority order: TruthfulQA first (fastest signal), then SWE-bench (highest impact), then HaluEval (requires most adaptation).

---

## 1. TruthfulQA

### Why it fits
- 817 questions designed to elicit false-but-plausible answers
- 13.3% of questions explicitly accept "I have no comment" as correct
- The adversarial subset (437 questions) maps directly to AFL's anti-bluffing goal
- Existing scoring distinguishes **truthful** vs. **informative** — abstention is always truthful but never informative

### AFL-specific metrics

| Metric | Definition |
|--------|-----------|
| Truthful Abstention Rate (TAR) | Among would-be-false answers, what fraction did AFL catch? |
| False Abstention Rate (FAR) | Among would-be-correct answers, what fraction did AFL wrongly suppress? |
| Selective Truthfulness | Truthfulness among answered-only questions |
| Coverage | Fraction of questions the model answers (vs. abstains) |
| Net Truthfulness Gain | Selective truthfulness improvement minus coverage cost |

### Category-to-status mapping

| AFL Status | TruthfulQA Categories |
|------------|----------------------|
| `CANNOT_VERIFY` | Misconceptions, Conspiracies, Paranormal, Superstitions, Fiction |
| `NEEDS_INFO` | Indexical Errors, Subjective |
| `BLOCKED_BY_POLICY` | Health, Law, Finance (advice-seeking) |
| Normal answer | History, Science, Language (factual) |

### Evaluation protocol

1. **Baseline run**: Model answers all 817 questions without AFL protocol (generation mode)
2. **Treatment run**: AFL protocol prepended to system prompt
3. **Score both** with GPT-judge for truthful/informative, plus manual AFL template classification
4. **Report**: Standard TruthfulQA metrics + AFL-specific metrics above
5. **Risk-coverage curve**: Plot selective truthfulness vs. coverage as AFL's abstention threshold varies

### Practical details
- **Dataset**: `truthfulqa/truthful_qa` on HuggingFace (Apache 2.0)
- **Size**: 817 questions — runnable in a single afternoon
- **Compute**: Minimal — generation + GPT-judge scoring
- **Known issue**: Data contamination risk with newer models. Use generation mode (not MC) as primary. Report MC1/MC2 as secondary.

### Expected outcome
AFL should increase Truthful% significantly (by catching trick questions) while decreasing Informative% moderately (by abstaining on answerable questions). The key metric is whether **Truthful * Informative%** improves — this would show AFL's abstention is selective, not blanket.

---

## 2. SWE-bench

### Why it fits
- Agentic coding context — exactly where AFL operates
- Current evaluation has a blind spot: **every system always submits a patch**, so false-fix rate = 1 - resolve rate
- No existing work measures honesty or abstention on SWE-bench
- AFL introduces a genuinely new capability: structured failure reports instead of broken patches

### AFL-specific metrics

| Metric | Definition |
|--------|-----------|
| Submission Precision | resolved / submitted (patches that actually work) |
| False-Fix Rate | unresolved / submitted (broken patches confidently submitted) |
| Honest Abstention Rate | correct abstentions / total abstentions |
| Wasted Compute | tokens spent on ultimately-failed patches |
| Failure Report Quality | manual scoring of AFL failure templates (1-5 scale) |

### Integration approach

The agent emits one of two outputs per instance:

```json
// Submit a patch
{"decision": "SUBMIT", "model_patch": "diff ..."}

// Abstain with structured failure
{"decision": "ABSTAIN", "failure_mode": {
  "status": "CANNOT_VERIFY",
  "blocked_because": "Cannot locate the relevant test file...",
  "to_proceed": "Need access to the test suite...",
  "safe_actions": ["1) Search for related files", "2) ..."]
}}
```

Harness modification: parse `decision` field. Track abstentions separately from failed patches.

### Evaluation protocol

1. Run on **SWE-bench Verified** (500 instances) — human-validated, good statistical power
2. **Baseline**: Standard agent (always submits patch)
3. **Treatment**: Same agent + AFL protocol (can abstain)
4. Compare: resolve rate, submission precision, false-fix rate
5. **McNemar's test** for statistical significance on paired instances
6. **Bootstrap CIs** for precision metrics

### Practical details
- **Dataset**: `princeton-nlp/SWE-bench_Verified` on HuggingFace
- **Size**: 500 instances
- **Compute**: ~$35-50 for evaluation (Docker-based harness), agent inference costs separate
- **Time**: ~13 hours at 8-way parallelism
- **Requirements**: x86_64, Docker, 120GB+ storage, 16GB RAM

### Expected outcome
AFL will likely **decrease** raw resolve rate slightly (some fixable instances get abstained on) but **dramatically increase** submission precision. The pitch: "AFL doesn't help agents fix more bugs, but when they can't fix a bug, they stop pretending they did."

### The novel contribution
No one has defined or measured "submission precision" on SWE-bench. This metric reframes the benchmark from "how many bugs can you fix?" to "how trustworthy are your patches?" — directly relevant to real-world deployment where a false fix is worse than no fix.

---

## 3. HaluEval

### Why it fits
- 35,000 examples across QA, dialogue, summarization, and general hallucination
- Directly measures hallucination — AFL's core target
- Novel angle: existing work uses HaluEval for detection; AFL uses it for prevention

### The adaptation challenge
HaluEval tests whether a model can **detect** hallucination in a given response. AFL **prevents** hallucination by triggering abstention. All HaluEval questions are answerable — the hallucination comes from generating wrong content, not from unanswerable queries.

**Reframing**: Withhold the knowledge context (source document, correct answer) and ask the model to answer the question directly. Without grounding knowledge, some questions become genuinely unverifiable — AFL should trigger abstention on those.

### Recommended approach

**Use QA paired split** (10,000 examples):

1. **Extract questions only** — strip the provided knowledge context
2. **Baseline**: Model answers without AFL. Score: did it hallucinate (match the hallucinated answer pattern)?
3. **Treatment**: Model answers with AFL. Score: did it abstain, answer correctly, or hallucinate?
4. **Metric**: Risk-coverage curve — as AFL abstention increases, does hallucination rate decrease proportionally?

### AFL-specific metrics

| Metric | Definition |
|--------|-----------|
| Hallucination Prevention Rate | Baseline hallucinations caught by AFL abstention |
| False Prevention Rate | Correct answers suppressed by AFL |
| Selective Accuracy | Accuracy among answered-only questions |
| Coverage@Hallucination=0 | Max coverage achievable with zero hallucinations |

### Practical details
- **Dataset**: `pminervini/HaluEval` on HuggingFace (MIT license)
- **Size**: 10,000 QA examples (recommended subset)
- **Compute**: Moderate — 10K inferences + scoring
- **Standard baseline**: ChatGPT gets 62.59% accuracy on QA detection

### Expected outcome
With knowledge withheld, AFL should abstain on questions where the model would otherwise hallucinate. The risk-coverage curve should show that AFL achieves near-zero hallucination at reasonable coverage levels (>60%).

---

## Implementation Phases

### Phase 1: TruthfulQA (1-2 days)
- [ ] Download dataset from HuggingFace
- [ ] Write evaluation harness (`eval/benchmarks/truthfulqa/`)
- [ ] Run baseline (no protocol) on target models
- [ ] Run treatment (AFL protocol) on same models
- [ ] Score with GPT-judge + AFL template classifier
- [ ] Generate risk-coverage curves and aggregate metrics
- [ ] Write results to `eval/benchmarks/truthfulqa/results.md`

### Phase 2: SWE-bench (1-2 weeks)
- [ ] Set up Docker-based SWE-bench harness
- [ ] Modify harness to accept abstention decisions
- [ ] Define submission precision and false-fix rate metrics
- [ ] Run on SWE-bench Verified (500 instances)
- [ ] Run baseline agent (always submit) vs. AFL agent (can abstain)
- [ ] Statistical analysis (McNemar's, bootstrap CIs)
- [ ] Write results to `eval/benchmarks/swebench/results.md`

### Phase 3: HaluEval (3-5 days)
- [ ] Download QA paired split
- [ ] Build knowledge-withholding pipeline
- [ ] Run baseline and treatment conditions
- [ ] Score against hallucinated/correct answer patterns
- [ ] Generate risk-coverage curves
- [ ] Write results to `eval/benchmarks/halueval/results.md`

### Phase 4: Paper / Write-up
- [ ] Unified results comparison across all 3 benchmarks + custom suite
- [ ] Update README with benchmark results
- [ ] Update `eval/results.md` with cross-benchmark summary

---

## Research references

Detailed benchmark-specific research reports:
- [`research/truthfulqa-afl-integration.md`](../research/truthfulqa-afl-integration.md)
- [`research/swe-bench-afl-integration.md`](../research/swe-bench-afl-integration.md)
- [`research/halueval-benchmark-analysis.md`](../research/halueval-benchmark-analysis.md)

Key papers:
- Lin et al. (2022). TruthfulQA: Measuring How Models Mimic Human Falsehoods. ACL 2022. arXiv:2109.07958
- Li et al. (2023). HaluEval: A Large-Scale Hallucination Evaluation Benchmark. EMNLP 2023. arXiv:2305.11747
- Jimenez et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024. arXiv:2310.06770
- Chowdhury et al. (2024). SWE-bench Verified. Blog post, OpenAI.
- Feng et al. (2024). "Know Your Limits": A Survey on Abstention in LLMs. TACL 2025.
- Deng et al. (2024). R-Tuning: Instructing LLMs to Refrain from Generating When Unsure. NAACL 2024 Outstanding Paper.
