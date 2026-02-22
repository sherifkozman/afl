# Comparison: Prototype concept vs this implementation

This repo includes the original concept prototype (`docs/prototype/agentfail.html`).
That prototype is valuable for communicating the idea, but it simplifies reality.

Below is an intentionally "unbiased" comparison.

## 1) Where the prototype is directionally correct

- **Core intuition holds**: agents tend to keep answering under pressure; a harnessed stop state can convert silent failure (hallucination) into explicit dialogue.
- **Tradeoff framing is right**: abstention reduces risk but can reduce utility if over-triggered.
- **Testing emphasis is right**: the concept focuses on observable outcomes (hallucinations vs guided failure).

## 2) What the prototype likely misses / abstracts away

- **No true confidence signal**: most agent frameworks don't expose calibrated confidence. A "confidence threshold" is typically a proxy.
- **Hook composition**: in real systems, multiple hooks and safety layers interact (often in parallel).
- **Syntactic vs semantic compliance**: requiring a template doesn't guarantee truthfulness inside the template.
- **Failure mode loops**: if not bounded, a Stop hook can trap the agent in a self-correction loop.

## 3) What this implementation adds

- **Enforcement mechanism**: Stop gate blocks completion until the protocol is used.
- **Observable triggers** instead of "confidence":
  - regex prompt heuristics for under-specification / unverifiability
  - tool failure signals
  - optional tests-as-gate
- **State storage that avoids repo pollution** (global per-project state fallback).

## 4) Where this implementation could still be wrong / out of context

- **Heuristic triggers may not generalize** across domains (false positives / negatives).
- **Stop gate checks headings only**; it can be satisfied while still being misleading.
- **User experience risk**: too many "NEEDS_INFO" responses can feel like the agent is timid.
- **Environment assumptions**: the agent runtime evolves; hooks and fields may change over time.

## 5) How to reconcile (practical consensus)

- Keep the prototype's conceptual model as a teaching tool.
- Measure reality with a prompt suite + rubric:
  - hallucination/bluff rate
  - false abstention rate
  - time-to-resolution

See `docs/04-testing.md` and `eval/`.
