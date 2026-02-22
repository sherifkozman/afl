# AFL (Agent Failure Mode)

**A "Failure Mode" harness for the agent runtime** that turns *hallucination pressure* into a **structured, recoverable stop state**.

When the agent hits a wall (unanswerable prompt, missing context, tool failure), AFL forces it to stop bluffing and respond in a deterministic template:

```
FAILURE MODE
Status: NEEDS_INFO | NEEDS_PERMISSION | BLOCKED_BY_POLICY | CANNOT_VERIFY
Blocked because:
- …
To proceed I need:
- …
Safe next actions (I can do now):
1) …
```

This repo is deliberately opinionated:
- **No "confidence score" fantasy.** We trigger failure mode using observable signals (prompt heuristics + tool failures + optional test gates).
- **Enforcement beats vibes.** The Stop hook blocks completion until the Failure Mode template is used.

> Not affiliated with Anthropic. Use at your own risk.

---

## Evaluation results

Tested across **7 models** (Gemini 2.5/3, GPT-5.x Codex, Claude Opus 4.6) on 7 adversarial prompts designed to induce hallucination, bluffing, and fabricated tool output.

| Metric | Baseline (no protocol) | With AFL | Change |
|--------|----------------------|----------|--------|
| Template compliance | 2.4% | **100%** | +97.6 pp |
| Bluff rate | 26.2% | **0%** | -26.2 pp |
| Mean score (0-10) | 2.98 | **9.33** | +6.35 |
| Correct status | 2.4% | 61.9% | +59.5 pp |

Key findings:
- **26% of baseline responses were outright bluffs** — models fabricated complete pytest sessions, invented bugs in non-existent code, and produced fake confidence numbers
- **The most hallucination-prone model showed the largest improvement** (+8.43 points)
- **The adversarial "act confident" prompt scored 0.33 baseline, 9.00 with AFL** — the protocol fully neutralized the attack
- **Zero false abstentions** — AFL never triggered on prompts where a direct answer was appropriate

Full data with per-model breakdowns, scoring rationale, and raw transcripts: [`eval/results.md`](eval/results.md)

---

## Why this exists

LLM agents are often trained/rewarded to "keep going," which makes *plausible completion* the default even when the task is under-specified or unverifiable.
AFL introduces an explicit **Agent Failure Mode**: "give up, but usefully."

Included in this repo is the original concept prototype (`docs/prototype/agentfail.html`) that motivated the approach.

---

## What's in the box

### Hooks (Python, stdlib-only)
- `afl_user_prompt.py` — prompt preflight: flags intrinsically unverifiable or under-specified prompts
- `afl_post_tool_failure.py` — if a tool fails, activates Failure Mode (prevents "it worked" bluffing)
- `afl_stop_gate.py` — enforcement: blocks stopping until Failure Mode template is used
- Optional:
  - `afl_pre_tool.py` — deny/ask rules for commands/paths (often overlaps with existing safety harnesses)
  - `afl_task_completed.py` — test gate on completion (exit code 2 blocks completion)

Shared utilities live in `hooks/afl_lib.py`.

### Policy (JSON)
`afl_policy.json` controls:
- feature flags (minimal vs full)
- regex triggers for "cannot verify" and "needs info"
- Stop gate requirements
- (optional) deny/ask command/path lists

### Rules
`rules/10-failure-mode.md` defines the protocol and "no bluffing" behavior for the agent runtime memory/rules.

---

## Quick start (global install)

### 1) Clone
```bash
git clone https://github.com/sherifkozman/afl.git
cd afl
```

### 2) Install into `~/.claude`
Minimal install (recommended):
```bash
python3 install_global.py
```

Full install (adds PreToolUse + TaskCompleted entries; still feature-gated by policy):
```bash
python3 install_global.py --full
```

### 3) Restart the host agent
The host agent snapshots hook config at startup. Restart after installing.

### 4) Verify
In the host agent:
- run `/hooks` to confirm `[User]` hooks are active
- toggle verbose mode (`Ctrl+O`) to see hook logs

---

## Project-level install (per repo)

See [`docs/03-installation.md`](docs/03-installation.md) for:
- copying `.claude/` into a repo
- project-local policy overrides
- avoiding conflicts with existing global hooks

---

## Testing

### Unit tests (hook logic)
```bash
python3 -m unittest discover -s tests -q
```

### Manual "no correct answer / cannot complete" prompts
See [`eval/prompt_suite.yaml`](eval/prompt_suite.yaml) and [`docs/04-testing.md`](docs/04-testing.md).

You're looking for:
- **no fabricated facts**
- **no claimed tool actions without evidence**
- **consistent Failure Mode template when triggered**

---

## Limitations (read this before you ship it)

AFL is a harness — not mind reading.

- **Heuristic prompt triggers** can miss edge cases (false negatives) or over-trigger (false positives).
- **Hook composition can be tricky**: the agent runtime runs matching hooks "in parallel," so overlapping PreToolUse hooks may interact in surprising ways.
- **No internal model confidence**: this is verifiability- and policy-driven.

Full discussion: [`docs/05-limitations.md`](docs/05-limitations.md).

---

## Repo map

- `hooks/` — agent runtime hook scripts
- `rules/` — agent runtime rules/memory fragments
- `settings/` — minimal/full hook config snippets
- `docs/` — thesis, design, testing, limitations, research references ([index](docs/REPORT.md))
- `eval/` — prompt suites, rubrics, and [results](eval/results.md) with raw transcripts
- `tests/` — unit tests for hook behavior
- `install_global.py` — safe global installer (backs up existing files)
- [`CHANGELOG.md`](CHANGELOG.md) — version history

---

## Contributing

PRs welcome. Please read:
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`SECURITY.md`](SECURITY.md)

---

## Research backing

AFL is aligned with research themes like **abstention**, **selective prediction**, and **hallucination detection**.
Start here: [`docs/06-research.md`](docs/06-research.md). See also the [literature assessment](research-assessment-llm-abstention.md).

---

## License

[MIT](LICENSE)
