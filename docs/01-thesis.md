# Thesis: Agent Failure Mode as a Harnessed Stop State

## Problem: the “can‑do trap”
Most LLM agents are trained (and rewarded) to continue responding. When they face:

- missing inputs (no repro steps, no logs, no access),
- unverifiable requests (“predict the exact price next Tuesday”),
- or failed tool actions,

the path of least resistance is often **plausible completion** rather than explicit uncertainty. This shows up as:
- fabricated facts,
- invented tool outputs,
- or confident but incorrect interpretations.

## Core claim: internal signals are necessary but insufficient
Research shows that LLMs do have meaningful internal confidence signals — verbalized confidence can be calibrated (Tian et al., EMNLP 2023) and models possess some self-knowledge about what they know (Kadavath et al., 2022). The claim here is not that these signals are useless.

The claim is that **internal signals alone are insufficient in multi-step agentic workflows**, where errors compound across steps, tool interactions introduce external failure points, context drifts over long horizons, and the agent can "bluff" about actions already taken. External enforcement provides complementary guarantees that internal calibration cannot: it is observable, auditable, and does not degrade under reasoning fine-tuning pressure.

## Hypothesis
If the agent is given an explicit **Failure Mode** with strict output constraints, then:

- hallucinations decrease (especially “bluffing”),
- clarification quality increases,
- and downstream task success improves after the missing inputs are provided,

at the cost of:
- higher refusal / “needs info” rate,
- potential user annoyance if triggers are too aggressive.

This is a calibrated trade: reduce risk by reducing coverage.

## Definition: Failure Mode (in this project)
Failure Mode is **not** “I refuse” and it is not “I’m not sure”.

Failure Mode is a **state with a protocol**:

1) **Stop**: do not fabricate or continue as if assumptions are facts.
2) **Expose blockers**: state what is missing or unverifiable.
3) **Request minimum inputs**: ask for the smallest set of info that makes progress possible.
4) **Offer safe next actions**: provide steps that do not require guessing.

The enforcement mechanism is external to the model: **a harness blocks completion until the protocol is followed** (Stop hook).

## Why this should help
In practice, hallucinations often happen because the agent is incentivized to “produce something” even when the situation is information-poor. Failure Mode changes the local incentives:

- Without Failure Mode: “produce plausible answer”
- With Failure Mode: “produce a structured plan to reduce uncertainty”

This is not a claim that the model becomes more knowledgeable. It is a claim that the **interaction becomes more honest and recoverable**.

## Novel contribution: typed terminal states for multi-step agent workflows
Most abstention research — SelfCheckGPT, AbstentionBench, Madhusudhan, and the Wen survey — studies single-turn QA: given one question, does the model correctly abstain or answer? Multi-step agent workflows are qualitatively different:

- Errors compound: a wrong assumption in step 2 poisons steps 3–10.
- Tool failures are external: the model cannot “know” a shell command failed unless it reads the output.
- Context drifts: long agentic traces cause the model to lose track of its own earlier commitments.
- Bluffing is easy: the agent can claim it ran tests, committed files, or called APIs when it did not.

The novel contribution of this project is **not** abstention itself (well-studied) but rather **typed, enforceable terminal states for multi-step agentic workflows**. When the harness triggers, the agent must declare a structured stop reason (NEEDS_INFO, NEEDS_PERMISSION, BLOCKED_BY_POLICY, CANNOT_VERIFY) and specify what it needs to resume. This is a protocol-level specification enforced externally via the Stop hook.

No existing agent framework provides this. LangChain, AutoGen, and CrewAI all terminate via blunt mechanisms — `max_iterations` limits or string-matching on output — with no typed reason, no required specification of missing inputs, and no enforcement that the agent actually stopped rather than silently continuing.

## What this project intentionally avoids
- Relying solely on self-reported confidence, which research shows is often miscalibrated (Xiong et al., ICLR 2024) and degrades under reasoning fine-tuning (AbstentionBench; Kirichenko et al., NeurIPS 2025).
- Claiming to eliminate hallucinations.
- Overfitting the harness to a single benchmark.

## Falsifiable predictions (how this can be wrong)
This thesis is wrong (or not useful) if, under realistic workloads:

- hallucination rates do not decrease,
- users abandon tasks because failure-mode triggers are too frequent,
- clarification questions are low quality and do not increase resolution,
- or the harness introduces new failure modes (e.g., hook conflicts) that outweigh benefits.

## Known gaps / open questions
- How do we best tune the tradeoff between “answer” and “ask” for different task classes?
- How do we detect under-specification robustly without excessive false positives?
- Can a verifier model (or self-consistency sampling) improve detection without excessive cost?

See `04-testing.md` and `05-limitations.md`.
