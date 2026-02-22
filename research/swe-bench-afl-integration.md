# SWE-bench Research Report for AFL Integration

## Executive Summary

SWE-bench is a benchmark of 2,294 real-world GitHub issues from 12 Python repositories, where LLM agents must generate patches to fix bugs. Current top systems resolve ~72-81% of the 500-instance "Verified" split, meaning **19-28% of all submissions are false fixes** -- patches submitted that do not actually resolve the issue. No existing system has an abstention mechanism; every system always submits a patch. This makes SWE-bench an ideal testbed for AFL (Agent Failure Mode), which could reduce wasted submissions by enabling agents to honestly declare "I cannot fix this" instead of submitting broken patches.

---

## 1. Dataset Structure

### Instance Counts (Confirmed)

| Split | Instances | Purpose |
|-------|-----------|---------|
| **SWE-bench Full** | 2,294 | Complete benchmark |
| **SWE-bench Lite** | 300 | Cheaper evaluation subset |
| **SWE-bench Verified** | 500 | Human-validated subset (by OpenAI, Aug 2024) |

### Repositories Covered (12 Python repos)

1. `django/django`
2. `scikit-learn/scikit-learn`
3. `matplotlib/matplotlib`
4. `sympy/sympy`
5. `pytest-dev/pytest`
6. `astropy/astropy`
7. `sphinx-doc/sphinx`
8. `pydata/xarray`
9. `psf/requests`
10. `pylint-dev/pylint`
11. `pallets/flask`
12. `mwaskom/seaborn`

### Instance Schema

Each instance is a JSON object with these fields:

```json
{
  "instance_id": "django__django-11848",
  "repo": "django/django",
  "base_commit": "abc123def456...",
  "problem_statement": "Natural language description of the bug (from GitHub issue/PR)",
  "hints_text": "Additional context from PR discussion (may be empty)",
  "patch": "diff --git a/... (gold/reference patch -- NOT given to agent)",
  "test_patch": "diff --git a/... (applied to set up test environment)",
  "FAIL_TO_PASS": ["tests/test_module.py::TestClass::test_method"],
  "PASS_TO_PASS": ["tests/test_other.py::test_other_method"],
  "environment_setup_commit": "...",
  "created_at": "2023-..."
}
```

**Key details:**
- `problem_statement`: The only input the agent sees (natural language bug description)
- `patch`: The gold/reference fix -- used for analysis only, never shown to the agent
- `test_patch`: Applied to the repo to ensure tests are runnable in the harness
- `FAIL_TO_PASS`: Tests that FAIL on `base_commit` and must PASS after the agent's fix
- `PASS_TO_PASS`: Tests that PASS on `base_commit` and must remain PASSING (regression check)

### How Instances Were Collected

1. Start from real GitHub bug-fix PRs in the 12 repos
2. Identify a `base_commit` where the bug exists
3. Extract the human patch that fixed it
4. Determine target tests: which fail before and pass after (`FAIL_TO_PASS`)
5. Identify regression tests that must remain passing (`PASS_TO_PASS`)
6. Add `test_patch` when needed for reproducibility in containers

### SWE-bench Verified (OpenAI, August 2024)

- 93 software developers manually screened samples
- Each sample labeled 3x by separate annotators
- **38.3%** flagged for underspecified problem statements
- **61.1%** flagged for unfair unit tests
- **68.3%** of Full SWE-bench samples filtered out total
- Resulting in 500 high-quality instances
- Difficulty labels: 196 "easy" (<15 min fix), 45 "hard" (>1 hour fix)

### HuggingFace Dataset Paths

- Full: `princeton-nlp/SWE-bench` -- https://huggingface.co/datasets/princeton-nlp/SWE-bench
- Lite: `princeton-nlp/SWE-bench_Lite` -- https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite
- Verified: `princeton-nlp/SWE-bench_Verified` -- https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified

---

## 2. Standard Evaluation

### Resolve Rate Calculation

```
resolve_rate = (instances_resolved) / (total_instances_evaluated) * 100
```

An instance is **resolved** if and only if:
1. The agent's patch applies cleanly to `base_commit`
2. ALL `FAIL_TO_PASS` tests now pass (bug is fixed)
3. ALL `PASS_TO_PASS` tests still pass (no regressions)

### Evaluation Pipeline (End-to-End)

**Step 1: Load instance** from HuggingFace datasets

**Step 2: Docker container setup**
- Clone repo at `base_commit`
- Install dependencies
- Apply `test_patch`

**Step 3: Agent receives `problem_statement`** (and optionally repo context)

**Step 4: Agent produces patch** (git diff format)

**Step 5: Patch applied** via `git apply`

**Step 6: Tests executed**
```bash
pytest -q <FAIL_TO_PASS tests>    # Must now pass
pytest -q <PASS_TO_PASS tests>    # Must still pass
```

**Step 7: Grading** -- binary resolved/unresolved per instance

### Prediction Format (JSONL)

```json
{"instance_id": "sympy__sympy-20590", "model_name_or_path": "gpt-4", "model_patch": "diff --git a/..."}
```

### Running Evaluation

```bash
pip install swebench

python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path predictions.jsonl \
    --max_workers 8 \
    --run_id my_evaluation
```

### Output Structure

```
evaluation_results/
  my_evaluation/
    results.json              # Overall metrics
    instance_results.jsonl    # Per-instance verdicts
    run_logs/                 # Per-instance logs
```

### Harness Source Code

- Main repo: https://github.com/SWE-bench/SWE-bench
- PyPI: https://pypi.org/project/swebench/
- CLI tool: https://github.com/swe-bench/sb-cli

---

## 3. Failure Analysis

### Taxonomy of SWE-bench Failures

When an agent submits a patch that does NOT resolve the issue, it falls into one of these categories:

| Category | Description | Prevalence |
|----------|-------------|------------|
| **Empty/no-op patch** | Agent outputs nothing, whitespace changes, or comments only | Common with tool failures |
| **Patch doesn't apply** | Syntax errors, wrong indentation, invalid diff format | ~5-15% of submissions |
| **Build breaks** | Missing imports, type errors, dependency damage | Varies by repo |
| **Wrong file/location** | Fix touches wrong module, wrong versioned path | Common localization failure |
| **Overfits to visible tests** | Passes available tests but fails hidden `FAIL_TO_PASS` tests | Most common false fix |
| **Breaks existing tests** | Fixes bug but introduces regressions in `PASS_TO_PASS` | Significant category |
| **Test-only "fix"** | Modifies tests instead of source code | Usually caught by harness |
| **Shallow pattern match** | Fixes symptom (exception) not cause (invariant) | Subtle false fix |

### Published Failure Analyses

1. **"An Empirical Study on LLM-based Agents for Automated Bug Fixing"** (arXiv:2411.10213)
   - Examines 6 repair systems on SWE-bench Verified
   - Analyzes fault localization accuracy, bug reproduction, and patch quality
   - Categorizes failures across: localization, reproduction, and repair dimensions

2. **"How Safe Are AI-Generated Patches?"** (arXiv:2507.02976)
   - First large-scale security analysis of LLM patches on SWE-bench (20,000+ patches)
   - Compares standalone LLM (Llama 3.3) vs agentic frameworks (OpenHands, AutoCodeRover, HoneyComb)
   - Finding: **Standalone LLMs introduce 9x more vulnerabilities than developer patches**
   - Uses Semgrep + Bandit + CodeQL with majority voting

3. **Agent-specific papers** (SWE-agent, Agentless, AutoCodeRover) each include qualitative failure buckets:
   - Localization errors (wrong files/regions)
   - Tool/interaction failures (shell issues, environment friction)
   - Patch correctness gaps
   - Long-horizon planning failures

### The False Fix Problem (Key AFL Insight)

**Every existing SWE-bench system always submits a patch.** There is no abstention mechanism.

Therefore, for any system with resolve rate R:
- **False-fix rate = 1 - R** (of submitted patches)
- A system with 50% resolve rate submits broken patches on 50% of instances
- Even SOTA at ~80% still has a 20% false-fix rate

This is the core thesis for AFL: **the cost of a false fix is not zero**. In real development:
- Wastes code reviewer time
- Gives false confidence ("the AI fixed it")
- May mask the real bug
- Can introduce security vulnerabilities (per arXiv:2507.02976)
- Delays the actual fix

---

## 4. Current SOTA (as of February 2026)

### SWE-bench Verified Leaderboard (Top Systems)

| System | Resolve Rate | Notes |
|--------|-------------|-------|
| Claude Opus 4.5 | ~80.9% | Self-reported |
| Claude Opus 4.6 | ~80.8% | Self-reported |
| MiniMax M2.5 | ~80.2% | |
| GPT-5.2 | ~80.0% | |
| GLM-5 | ~77.8% | |
| Claude Sonnet 4.5 | ~77.2% | |
| Kimi K2.5 | ~76.8% | |
| Gemini 3 Pro | ~76.2% | |

### SWE-bench Bash-Only (Feb 2026)

| System | Resolve Rate |
|--------|-------------|
| Claude 4.5 Opus (high reasoning) | 76.8% |
| Gemini 3 Flash (high reasoning) | 75.8% |

### Live-SWE-agent Leaderboard

| System | Resolve Rate |
|--------|-------------|
| Claude Opus 4.5 + Live-SWE-agent | 79.2% |
| Gemini 3 Pro + Live-SWE-agent | 77.4% |

### Historical Context (key milestones)

- **Early 2024**: SWE-agent (GPT-4) ~12% on Full, ~18% on Lite
- **Mid 2024**: Agentless ~27% on Lite; AutoCodeRover ~19% on Lite ($0.43/instance)
- **Late 2024**: Claude 3.5 Sonnet-based systems ~49-55% on Verified
- **2025**: Systems cross 60-70% on Verified
- **Early 2026**: Top systems at ~80% on Verified

### False-Fix Rate by System (Derived)

| System | Resolve Rate | False-Fix Rate (= patches that don't resolve) |
|--------|-------------|-------|
| Top SOTA (~80%) | 80% | **20% of submissions are false fixes** |
| Mid-tier (~60%) | 60% | **40% of submissions are false fixes** |
| Early systems (~20%) | 20% | **80% of submissions are false fixes** |

---

## 5. AFL-Specific Metrics Design

### Core Metrics

Let N = total instances, S = instances where agent submitted a patch, A = instances where agent abstained, R = instances resolved (among submitted).

#### 1. False-Fix Rate (FFR)
```
FFR = |S - R| / |S| = (submitted but unresolved) / (total submitted)
```
**Lower is better.** Measures the "waste rate" of submissions.

Baseline (no abstention): FFR = 1 - resolve_rate

#### 2. Submission Precision (SP)
```
SP = |R| / |S| = (resolved) / (total submitted)
```
**Higher is better.** SP = 1 - FFR. "Of the patches I submit, what fraction actually work?"

#### 3. Abstention Rate (AR)
```
AR = |A| / N = (abstained) / (total instances)
```
**Context-dependent.** Too low = not abstaining enough. Too high = abstaining on solvable problems.

#### 4. Resolve Rate (RR) -- Standard Metric
```
RR = |R| / N
```
**Higher is better.** Must not decrease significantly with AFL.

#### 5. Honest Abstention Rate (HAR)
```
HAR = |correct abstentions| / |A|
```
Where "correct abstention" = instance that baseline system also fails to solve.

#### 6. Wasted Submission Rate (WSR)
```
WSR = |S - R| / N = (wasted submissions) / (total)
```
**Lower is better.** This is the key metric for AFL -- reducing useless patch submissions.

### Comparison Framework: Baseline vs AFL

Run the same agent on the same 300/500 instances in two modes:

| Metric | Baseline Agent | AFL Agent | Delta | Direction |
|--------|---------------|-----------|-------|-----------|
| Resolve Rate (RR) | X% | Y% | Y-X | Should stay same or decrease slightly |
| False-Fix Rate (FFR) | 1-X% | ? | Lower | **Key improvement** |
| Submission Precision (SP) | X% | ? | Higher | **Key improvement** |
| Abstention Rate | 0% | ? | >0% | Expected |
| Wasted Submissions (WSR) | 1-X% | ? | Lower | **Key improvement** |

### The Key Hypothesis

> AFL should INCREASE Submission Precision (SP) while maintaining or only slightly decreasing Resolve Rate (RR). The agent should abstain on instances it would have gotten wrong anyway, reducing Wasted Submission Rate (WSR).

### Statistical Considerations

With 300 instances (Lite) or 500 instances (Verified):

- **McNemar's test**: Paired comparison of resolved vs not-resolved per instance
- **Bootstrap confidence intervals**: Resample instance IDs with replacement, compute metric deltas
- **Effect size**: With n=300, can detect ~10 percentage point differences with 80% power
- **Recommendation**: Use SWE-bench Verified (500 instances) for better statistical power

### Scoring Function (Optional)

To capture the cost asymmetry:

```
score = sum over instances of:
  +1  if resolved (correct submission)
  -lambda  if submitted but unresolved (false fix, lambda > 0)
  0  if abstained
```

Where lambda captures the cost of a false fix. lambda=0.5 means a false fix costs half as much as a correct fix is worth. lambda=1 means symmetric cost.

---

## 6. Integration Approach

### Where AFL Injects in the Pipeline

```
Standard SWE-bench Agent Pipeline:
  1. Receive problem_statement
  2. Explore codebase (search, read files)
  3. Localize bug (identify files/functions)
  4. Generate patch (edit code)
  5. [Optional: Run tests locally]
  6. ALWAYS submit patch  <-- THIS IS WHERE AFL INTERVENES

AFL-Enhanced Pipeline:
  1. Receive problem_statement
  2. Explore codebase
  3. Localize bug
  4. Generate patch
  5. [Optional: Run tests locally]
  6. AFL DECISION POINT:
     - Confidence >= threshold? -> SUBMIT patch
     - Confidence < threshold?  -> ABSTAIN with structured failure report
```

### AFL Failure Template (Adapted for SWE-bench)

When the agent decides to abstain, it outputs:

```json
{
  "instance_id": "django__django-11848",
  "decision": "ABSTAIN",
  "failure_mode": "CANNOT_LOCALIZE | CANNOT_REPRODUCE | LOW_CONFIDENCE | ENVIRONMENT_ERROR",
  "status": "NEEDS_INFO | BLOCKED_BY_COMPLEXITY | CANNOT_VERIFY",
  "evidence": {
    "files_examined": ["django/db/models/query.py", "django/db/models/sql/compiler.py"],
    "commands_run": ["grep -r 'QuerySet' django/db/", "pytest tests/queries/"],
    "observations": ["Found 3 potentially relevant locations but unclear which is root cause"],
    "test_results": "FAIL_TO_PASS tests could not be reproduced on base_commit"
  },
  "blocked_because": "Multiple candidate locations identified but insufficient signal to determine correct fix",
  "safe_next_actions": [
    "Investigate django/db/models/sql/compiler.py lines 400-450",
    "Check if issue is related to QuerySet.union() method",
    "Review similar issues in Django issue tracker"
  ]
}
```

### Harness Modifications

The evaluation harness needs minimal changes:

```python
# In the evaluation loop:
import json

def evaluate_instance(instance, agent_output):
    output = json.loads(agent_output)

    if output.get("decision") == "ABSTAIN":
        return {
            "instance_id": instance["instance_id"],
            "status": "abstained",
            "failure_mode": output.get("failure_mode"),
            "resolved": False,
            "submitted": False
        }

    # Standard evaluation path
    patch = output.get("model_patch") or output.get("patch")
    apply_result = apply_patch(patch)
    if not apply_result:
        return {"status": "patch_apply_failed", "resolved": False, "submitted": True}

    f2p_pass = run_tests(instance["FAIL_TO_PASS"])
    p2p_pass = run_tests(instance["PASS_TO_PASS"])

    return {
        "instance_id": instance["instance_id"],
        "status": "resolved" if (f2p_pass and p2p_pass) else "unresolved",
        "resolved": f2p_pass and p2p_pass,
        "submitted": True
    }
```

### Predictions File Format (Extended for AFL)

Standard format (always submits):
```jsonl
{"instance_id": "X", "model_name_or_path": "agent-v1", "model_patch": "diff..."}
```

AFL-extended format:
```jsonl
{"instance_id": "X", "model_name_or_path": "agent-afl", "model_patch": "diff...", "decision": "SUBMIT"}
{"instance_id": "Y", "model_name_or_path": "agent-afl", "model_patch": "", "decision": "ABSTAIN", "failure_mode": "CANNOT_LOCALIZE", "evidence": {...}}
```

### Agent-Side Implementation

For SWE-agent-style frameworks, inject AFL at the "submit" action:

```python
# In the agent's action loop (pseudo-code)
class AFLAgent:
    def decide_submission(self, patch, context):
        confidence = self.estimate_confidence(patch, context)

        if confidence >= self.threshold:
            return {"decision": "SUBMIT", "model_patch": patch}
        else:
            return {
                "decision": "ABSTAIN",
                "failure_mode": self.classify_failure(context),
                "evidence": self.gather_evidence(context)
            }

    def estimate_confidence(self, patch, context):
        """
        Heuristics for confidence estimation:
        1. Did the agent successfully localize the bug? (file found, function found)
        2. Did local tests pass after the patch?
        3. Is the patch non-trivial? (not just exception swallowing)
        4. Does the patch match the problem description semantically?
        5. Self-evaluation: ask the LLM "does this patch actually fix the described issue?"
        """
        signals = []
        signals.append(self.localization_confidence)
        signals.append(self.test_pass_rate)
        signals.append(self.patch_quality_score)
        return aggregate(signals)
```

---

## 7. Practical Considerations

### Recommended Split: SWE-bench Verified (500 instances)

| Factor | Lite (300) | Verified (500) | Full (2,294) |
|--------|-----------|---------------|-------------|
| Compute cost (eval only) | ~$20-30 | ~$35-50 | ~$140-210 |
| Wall time (8-way parallel) | ~8 hours | ~13 hours | ~57 hours |
| Statistical power | Moderate | Good | Excellent |
| Instance quality | Mixed | High (human-validated) | Mixed |
| **Recommendation** | Development/debugging | **Primary evaluation** | Full paper |

### System Requirements

- x86_64 machine (or ARM with local image builds: `--namespace ''`)
- 120GB+ free storage
- 16GB RAM minimum
- 8+ CPU cores
- Docker Desktop (macOS) or Docker Engine (Linux)
- No GPU needed for evaluation (only for LLM inference)

### Known Gotchas

1. **Docker on macOS**: File sharing is slow; use local paths, avoid large bind mounts
2. **Python version mismatches**: Some repos need specific Python versions (3.8 vs 3.11)
3. **Flaky tests**: Time-dependent, network-dependent, or race condition tests exist
4. **ARM builds**: Default images are x86_64; use `--namespace ''` on M-series Macs
5. **Storage bloat**: Docker images can consume 100-300GB; use `--clean True` and `--cache_level base`
6. **Test timeouts**: Some tests run >30 min; harness enforces timeout (usually 1800s)
7. **Submodules**: Some repos need `git submodule update --init --recursive`

### Cloud Evaluation Options

```bash
# Modal (simplest cloud option)
pip install modal swebench[modal]
modal setup
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path predictions.jsonl \
    --parallelism 10 \
    --modal true

# sb-cli (official tool)
pip install sb-cli
sb login
sb submit --predictions predictions.jsonl
```

---

## 8. Related Work

### Key Papers

| Paper | Authors | Venue | ArXiv | Relevance to AFL |
|-------|---------|-------|-------|-------------------|
| **SWE-bench** | Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan | ICLR 2024 (Oral) | 2310.06770 | The benchmark itself |
| **SWE-agent** | Yang, Jimenez, Wettig, Lieret, Yao, Narasimhan, Press | NeurIPS 2024 | 2405.15793 | Agent framework with error analysis |
| **Agentless** | Xia, Deng, Dunn, Zhang | FSE 2025 | 2407.01489 | Localize->Edit->Verify pipeline |
| **AutoCodeRover** | Zhang, Ruan, Fan, Roychoudhury | ISSTA 2024 | 2404.05427 | Program analysis + LLM approach |
| **LLM Agents for Bug Fixing** | (Various) | arXiv 2024 | 2411.10213 | Systematic failure analysis of 6 systems |
| **AI Patch Security** | (Various) | arXiv 2025 | 2507.02976 | LLMs introduce 9x more vulnerabilities |

### Honesty/Calibration Literature (Adjacent)

- **Selective prediction / abstention**: Geifman & El-Yaniv (risk-coverage framework)
- **LLM calibration**: Temperature scaling, logprob-based confidence
- **Self-consistency**: Wang et al. (arXiv:2203.11171) -- agreement rate as confidence proxy
- **Code verification**: CodeRL (Le et al., NeurIPS 2022, arXiv:2207.01780) -- execution feedback for generation
- **AlphaCode**: Li et al. (Science 2022) -- massive sampling + filtering/ranking

### Gap in Literature

**No existing work measures honesty/abstention on SWE-bench.** All systems always submit a patch. No benchmark in the code generation space rewards abstention. This is the novel contribution space for AFL.

---

## 9. Experimental Design for AFL Paper

### Proposed Experiment

1. **Baseline**: Run agent (e.g., Claude Sonnet + SWE-agent scaffold) on SWE-bench Verified (500 instances). Always submit patches.

2. **AFL-enhanced**: Same agent + AFL protocol. Agent can abstain with structured failure report.

3. **Measure**:

| Metric | Expected Baseline | Expected AFL | Expected Delta |
|--------|------------------|-------------|----------------|
| Resolve Rate | ~50-55% | ~48-53% | Slight decrease (lost a few correct-but-uncertain) |
| Submission Precision | ~50-55% | ~70-85% | **Large increase** |
| False-Fix Rate | ~45-50% | ~15-30% | **Large decrease** |
| Abstention Rate | 0% | ~20-35% | New metric |
| Wasted Submissions | ~45-50% | ~10-20% | **Large decrease** |

4. **Qualitative analysis** of abstention reports: Are they useful? Do they provide actionable debugging information?

5. **Ablation**: Vary the confidence threshold to produce a precision-recall curve (submission precision vs resolve rate)

### The Pitch

> "Current SWE-bench evaluation rewards bluffing: agents always submit patches, and ~20-50% of those patches are useless false fixes. AFL introduces an honest abstention mechanism that dramatically increases submission precision -- the fraction of submitted patches that actually work -- while providing structured failure reports that help developers understand why the agent couldn't fix an issue."

---

## References

1. SWE-bench website: https://www.swebench.com/
2. SWE-bench GitHub: https://github.com/SWE-bench/SWE-bench
3. SWE-bench paper (ICLR 2024): https://arxiv.org/abs/2310.06770
4. SWE-bench Verified (OpenAI): https://openai.com/index/introducing-swe-bench-verified/
5. SWE-agent (NeurIPS 2024): https://arxiv.org/abs/2405.15793
6. Agentless (FSE 2025): https://arxiv.org/abs/2407.01489
7. AutoCodeRover (ISSTA 2024): https://arxiv.org/abs/2404.05427
8. LLM Bug Fixing Study: https://arxiv.org/abs/2411.10213
9. AI Patch Security Study: https://arxiv.org/abs/2507.02976
10. SWE-bench evaluation guide: https://www.swebench.com/SWE-bench/guides/evaluation/
11. SWE-bench leaderboard: https://www.swebench.com/
12. Live-SWE-agent leaderboard: https://live-swe-agent.github.io/
13. Epoch AI SWE-bench tracker: https://epoch.ai/benchmarks/swe-bench-verified
14. SWE-bench Verified leaderboard (llm-stats): https://llm-stats.com/benchmarks/swe-bench-verified
