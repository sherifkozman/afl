# Roadmap

This project is intentionally minimal. Possible next steps:

## 1) Better "cannot verify" detection
- Replace regex-only triggers with richer heuristics:
  - detect "exact future values" more robustly
  - detect "missing repo access" / "missing logs" patterns
- Allow per-project prompt trigger packs

## 2) Verifier hook (optional)
Add a prompt-based Stop verifier that flags:
- claims of tool execution without evidence
- factual assertions without citations in "research mode"

Tradeoff: added latency and cost.

## 3) Scoring tooling
- `scripts/score_transcript.py` that:
  - checks Failure Mode template compliance
  - detects bluff phrases ("I ran tests…") without tool logs
  - outputs summary metrics

## 4) Cross-agent ports
- Codex equivalent: AGENTS.md + rules + output-schema enforcement
- Gemini equivalent: tool restrictions + logging + rubric scoring

## 5) Benchmarks
- Publish a community prompt suite and encourage PRs:
  - unanswerable prompts
  - under-specified prompts
  - tool-failure recovery tasks
  - high-stakes action confirmation tests
