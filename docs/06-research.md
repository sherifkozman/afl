# Research & Prior Art

AFL (Agent Failure Mode) is a practical harness inspired by work on:

- **Abstention** ("knowing when not to answer")
- **Selective prediction** (risk vs coverage tradeoffs)
- **Hallucination detection** (especially black-box settings)
- **Calibration** (confidence should match correctness)

This repo is not a research paper. It is an engineered harness with an evaluation plan.

## Key references

### Abstention / "when to not answer"
- Madhusudhan et al. (2024) *Do LLMs Know When to NOT Answer? Investigating Abstention Abilities of Large Language Models*
  (Introduces Abstain-QA dataset and an Answerable-Unanswerable Confusion Matrix evaluation framework for black-box abstention evaluation.)
  https://arxiv.org/abs/2407.16221

- Wen et al. (TACL 2025) *Know Your Limits: A Survey of Abstention in Large Language Models*
  ACL Anthology: https://aclanthology.org/2025.tacl-1.26/
  Publisher DOI landing page: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00754/131566/Know-Your-Limits-A-Survey-of-Abstention-in-Large

- Kirichenko et al. (NeurIPS 2025) *AbstentionBench*
  Shows that reasoning fine-tuning degrades abstention ability by 24%, making the tradeoff between capability and appropriate refusal a first-class design concern.
  https://arxiv.org/abs/2506.09038

### Self-knowledge and calibration
- Kadavath et al. (2022) *Language Models (Mostly) Know What They Know*
  Foundational work showing that LLMs have genuine, if imperfect, self-knowledge about their own correctness; motivates using self-assessment as a signal while acknowledging its limits.
  https://arxiv.org/abs/2207.05221

- Xiong et al. (ICLR 2024) *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs*
  Demonstrates that LLMs are systematically overconfident when asked to self-report confidence, which is why AFL uses external verification rather than verbalized confidence as the primary gate.
  https://arxiv.org/abs/2306.13063

- Tian et al. (EMNLP 2023) *Just Ask for Calibration*
  Shows that verbalized confidence CAN be well-calibrated under certain prompting conditions. A counterpoint the thesis must acknowledge — see "Counterpoints and alternative approaches" below.
  https://aclanthology.org/2023.emnlp-main.330/

### Calibration
- Guo et al. (2017) *On Calibration of Modern Neural Networks*
  https://arxiv.org/abs/1706.04599

### Uncertainty quantification
- Kuhn et al. (ICLR 2023) *Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation*
  Introduces semantic entropy as an internal uncertainty quantification method that clusters semantically equivalent generations before measuring entropy, representing the strongest known internal UQ signal for free-text output.
  https://arxiv.org/abs/2302.09664

### Selective prediction and verification
- "Trust or Escalate" (ICLR 2025 Oral)
  Selective evaluation framework where a cheaper judge model either trusts its own rating or escalates to a stronger model, with provable coverage-agreement guarantees. The cascade principle — act if confident, escalate if not — is analogous to AFL's approach of proceeding when safe and stopping when uncertain.
  https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf

- Lightman et al. (ICLR 2024) *Let's Verify Step by Step*
  Process reward models as external step-level verification; supports the AFL design choice of checking intermediate tool steps rather than only final output.
  https://arxiv.org/abs/2305.20050

### Hallucination detection (black-box)
- Manakul et al. (2023) *SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models*
  https://arxiv.org/abs/2303.08896

### Multi-agent debate
- Du et al. (ICML 2024) *Improving Factuality and Reasoning in Language Models through Multiagent Debate*
  Multi-agent debate as an alternative mechanism for reducing hallucination; contrasts with AFL's single-agent external-enforcement approach.
  https://arxiv.org/abs/2305.14325

## Agent-specific failure research

- *How Do LLMs Fail In Agentic Scenarios?* (2024)
  Taxonomizes failure modes specific to LLM agents (planning errors, tool misuse, compounding mistakes across steps) that motivate why single-turn abstention research is insufficient for agentic harnesses.
  https://arxiv.org/abs/2512.07497

- *Why Do Multi-Agent LLM Systems Fail?* (2025)
  Empirical analysis of failure patterns in multi-agent pipelines; finds that inter-agent trust and error propagation are qualitatively different from single-agent failures, reinforcing the need for explicit failure-mode enforcement at the harness level.
  https://arxiv.org/abs/2503.13657

## Counterpoints and alternative approaches

The thesis must honestly engage with evidence that internal confidence signals can work:

- **Internal confidence CAN work in some settings.** Tian et al. (EMNLP 2023) show that verbalized confidence is well-calibrated under careful prompting. AFL does not claim internal signals are useless — it claims they are insufficient as the sole enforcement mechanism in agentic workflows.

- **Semantic entropy provides a strong internal UQ signal.** Kuhn et al. (ICLR 2023) show that measuring entropy over semantically clustered generations substantially outperforms naive sampling-based uncertainty. This is the most credible internal alternative to external verification.

- **Models contain genuine self-knowledge.** Kadavath et al. (2022) establish that LLMs do have meaningful, if imperfect, introspective access to their own likely correctness. This finding motivates using self-assessment as one input signal rather than discarding it entirely.

The counterarguments that motivate AFL's external-enforcement design:

- **Reasoning training degrades abstention.** AbstentionBench (Kirichenko et al., NeurIPS 2025) shows a 24% degradation in abstention ability after reasoning fine-tuning, meaning the most capable models may also be the worst at refusing appropriately.

- **LLMs are overconfident in self-reporting.** Xiong et al. (ICLR 2024) show systematic overconfidence when confidence is elicited directly, making self-report an unreliable primary gate.

- **External step verification outperforms self-assessment.** Lightman et al. (ICLR 2024) demonstrate that process-level reward models catch errors that self-evaluation misses, supporting AFL's tool-result and test-pass gates over introspective confidence.

## Agent runtime docs (implementation substrate)
AFL is implemented using agent runtime hooks and memory/rules.

- Hooks reference (events, schemas, decision control, parallel execution):
  https://code.claude.com/docs/en/hooks

- Memory management (CLAUDE.md imports, .claude/rules/, user-level rules):
  https://code.claude.com/docs/en/memory

## Relationship to this repo

AFL does **not** assume access to token probabilities or internal confidence.

Most abstention research targets single-turn QA: a model receives a question and must decide whether to answer or refuse. This project targets multi-step agentic workflows, where the failure dynamics are qualitatively different. Errors compound across steps, tool interactions introduce external state that the model cannot fully introspect, and a single misjudgment early in a plan can corrupt all downstream work. The agent-specific failure literature (see above) confirms this distinction is empirically meaningful, not merely theoretical.

AFL approximates "should abstain" using:
- whether the request is verifiable or under-specified (prompt preflight)
- whether tools failed (tool failure preflight)
- whether tests fail (optional completion gate)

Then it uses external enforcement (Stop gate) to require a structured failure response.
