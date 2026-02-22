# Limitations & Failure Cases

AFL reduces *some* hallucinations by changing how the agent behaves under uncertainty. It does not guarantee truth.

## 1) No internal confidence
The agent runtime does not expose a reliable "confidence score" to hooks. AFL therefore uses:
- heuristic prompt triggers
- tool failure signals
- optional test gates

This means:
- false negatives: some unanswerable prompts won't match triggers
- false positives: some safe prompts may be flagged

## 2) Hook composition conflicts
The agent runtime can run multiple matching hooks "in parallel". If you have overlapping global hooks (especially `PreToolUse`), you can get ambiguous interactions.

Mitigation:
- start with minimal install
- keep `features.preToolUse=false` unless needed
- add one guard at a time and re-run the prompt suite

## 3) Template enforcement is syntactic
Stop gate checks for required headings. A malicious or careless agent could include headings but still smuggle fabricated content inside.

Mitigation ideas:
- add a verifier hook (prompt-based) that checks for unsupported claims
- scan for "I ran tests" phrases unless tool logs show such execution

## 4) Under-specification detection is hard
Regex triggers are a blunt tool. Real under-specification depends on domain context and what the agent can actually access.

Mitigation ideas:
- project-specific policies
- richer trigger logic (e.g., detect missing files/repo access, missing error logs)

## 5) "Give up" can be annoying
Over-abstention reduces utility. Failure Mode is a tradeoff knob.

Mitigation:
- tune triggers per project
- separate policies for low-stakes vs high-stakes workflows
- measure false abstention explicitly (don't guess)

## 6) Not a sandbox
AFL does not provide OS isolation. Use containers, least-privilege creds, and review for high-stakes operations.

## 7) Scope: multi-step agent workflows, not single-turn QA
Most academic abstention research evaluates single-turn question answering, where the model produces one response and the evaluation is complete. This project targets multi-step agent workflows, where the failure dynamics are qualitatively different:

- **Error compounding**: downstream actions build on fabricated prior state, so a single misjudgment early in a plan corrupts all subsequent steps.
- **Tool bluffing**: the agent can claim it ran tests, committed files, or called APIs when it did not — a failure mode absent from QA settings.
- **Context drift**: long agentic traces cause the model to lose track of its own earlier commitments and constraints.

The evaluation methodology — prompt suite, hook-gate rubric, state tracking — is designed for this agent context and does not map cleanly onto QA benchmarks. Results and mitigations from single-turn abstention research should be applied cautiously and re-validated against agentic scenarios.

## 8) Taxonomy completeness
The current four status codes (`NEEDS_INFO`, `NEEDS_PERMISSION`, `BLOCKED_BY_POLICY`, `CANNOT_VERIFY`) cover the most common failure modes observed across the tested agent workflows. They are not exhaustive. Additional codes — `LOOP_DETECTED`, `BUDGET_EXCEEDED`, `TOOL_UNAVAILABLE` — are under consideration as more agent workflows are studied and new failure patterns emerge. The taxonomy should be treated as a living artifact: expand it when a recurring failure mode cannot be adequately expressed by an existing status.
