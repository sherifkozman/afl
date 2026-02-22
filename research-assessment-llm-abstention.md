# Academic Landscape Assessment: LLM Abstention, Selective Prediction, and Agent Failure Modes

**Date**: 2026-02-21
**Purpose**: Validate academic grounding of thesis project claims

---

## SECTION 1: VERIFICATION OF CITED WORKS

### 1.1 Madhusudhan et al. (2024) -- "Do LLMs Know When to NOT Answer?"

**Status: REAL -- Minor characterization concerns**

- **Full title**: "Do LLMs Know When to NOT Answer? Investigating Abstention Abilities of Large Language Models"
- **Authors**: Nishanth Madhusudhan, Sathwik Tejaswi Madhusudhan, Vikas Yadav, Masoud Hashemi
- **Venue**: arXiv July 2024 (2407.16221), later published at COLING 2025 (31st International Conference on Computational Linguistics)
- **Source**: [arXiv](https://arxiv.org/abs/2407.16221) | [ACL Anthology](https://aclanthology.org/2025.coling-main.627/)

**What it actually found:**
- Introduced "Abstention Ability" (AA) as a formal concept -- the capability to withhold responses when uncertain
- Created **Abstain-QA** dataset with varied question types (answerable/unanswerable), domains (well/under-represented), and task types (fact-centric/reasoning)
- Proposed the **Answerable-Unanswerable Confusion Matrix (AUCM)** -- this is a *confusion matrix*, NOT a curve metric. The name AUCM refers to the matrix structure, not "Area Under" anything
- Tested three prompting strategies: Strict Prompting, Verbal Confidence Thresholding, Chain-of-Thought (CoT)
- **Key finding**: Even GPT-4 and Mixtral 8x22b struggle with abstention, but Strict Prompting and CoT can improve it
- Uses a **black-box evaluation approach** -- no access to token probabilities needed

**IMPORTANT CLARIFICATION**: If the thesis describes AUCM as "Area Under the Coverage-Merit curve," that is **incorrect**. AUCM stands for "Answerable-Unanswerable Confusion Matrix." It is a confusion matrix framework, not a curve-based metric like AUC-ROC. This is a factual error that must be corrected.

### 1.2 Wen et al. (TACL 2025) -- "Know Your Limits"

**Status: REAL -- Correctly identified venue**

- **Full title**: "Know Your Limits: A Survey of Abstention in Large Language Models"
- **Authors**: Bingbing Wen, Jihan Yao, Shangbin Feng, Chenjun Xu, Yulia Tsvetkov, Bill Howe, Lucy Lu Wang
- **Venue**: Transactions of the Association for Computational Linguistics (TACL), Volume 13, pp. 529-556, 2025
- **DOI**: 10.1162/tacl_a_00754
- **Source**: [ACL Anthology](https://aclanthology.org/2025.tacl-1.26/) | [MIT Press](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00754/131566)

**What it covers:**
- Introduces a **three-perspective framework** for examining abstention: (1) the query, (2) the model, (3) human values
- Organizes literature on abstention **methods**, **benchmarks**, and **evaluation metrics**
- Discusses merits and limitations of prior work
- Identifies future research directions including whether abstention can be a **meta-capability** that transcends specific tasks/domains
- Covers optimization of abstention abilities in specific contexts

**Assessment**: This is a legitimate, high-quality survey published in a top-tier CL journal. It is the definitive reference for the field as of 2025.

### 1.3 Manakul et al. (2023) -- "SelfCheckGPT"

**Status: REAL -- Correctly characterized**

- **Full title**: "SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models"
- **Authors**: Potsawee Manakul, Adian Liusie, Mark Gales
- **Venue**: EMNLP 2023 (main conference), Singapore
- **Source**: [ACL Anthology](https://aclanthology.org/2023.emnlp-main.557/) | [arXiv](https://arxiv.org/abs/2303.08896)

**What it does:**
- Detects hallucinations via **self-consistency**: sample multiple generations for the same prompt, check if claims are consistent across samples
- **Zero-resource**: no external knowledge base or retrieval system needed
- **Black-box**: only needs model outputs, no logit access required
- Uses multiple consistency measures: n-gram overlap, BERTScore, NLI-based entailment
- Evaluated on WikiBio dataset (GPT-3 generated biographies)
- **Key finding**: NLI/BERTScore variants outperform lexical overlap; achieves higher AUC-PR than grey-box methods for sentence-level hallucination detection
- **Known limitation**: Fails when the model is *consistently* wrong across samples (correlated hallucinations)

---

## SECTION 2: CRITICAL MISSING PRIOR ART

The following works are highly relevant and their absence would be a significant gap in any thesis on this topic.

### 2.1 Foundational Works (Must-Cite)

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| **Kadavath et al., "Language Models (Mostly) Know What They Know"** | arXiv 2022 (Anthropic) | Foundational study of LLM self-knowledge. Shows models contain usable signals about their own correctness, but turning that into reliable abstention is nontrivial. Trains P(IK) -- "probability that I know." The "(Mostly)" qualifier is critical. [arXiv](https://arxiv.org/abs/2207.05221) |
| **Kuhn et al., "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in NLG"** | ICLR 2023 (Spotlight) | Introduces **semantic entropy** -- uncertainty measure that groups semantically equivalent responses. More predictive of correctness than token-level entropy. Fundamental advance in UQ for LLMs. [arXiv](https://arxiv.org/abs/2302.09664) |
| **Tian et al., "Just Ask for Calibration"** | EMNLP 2023 | Shows that **verbalized confidence** from RLHF-LMs is often *better calibrated* than conditional probabilities. Reduces expected calibration error by ~50%. Directly relevant to internal confidence approaches. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.330/) |
| **Xiong et al., "Can LLMs Express Their Uncertainty?"** | ICLR 2024 | Systematic framework for confidence elicitation. **Key finding: LLMs are overconfident when verbalizing confidence.** Proposes mitigation strategies. Directly challenges the reliability of internal confidence. [arXiv](https://arxiv.org/abs/2306.13063) |

### 2.2 Agent Failure Modes (High Priority -- 2024-2025)

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| **"How Do LLMs Fail In Agentic Scenarios?"** | arXiv Dec 2024 (2512.07497) | Analyzes 900 execution traces. Identifies four failure archetypes: *premature action without grounding*, *over-helpfulness*, *distractor-induced context pollution*, *fragile execution under load*. Model scale does NOT predict agentic robustness. [arXiv](https://arxiv.org/abs/2512.07497) |
| **Cemri et al., "Why Do Multi-Agent LLM Systems Fail?"** | arXiv Mar 2025 (2503.13657) | First systematic evaluation using Grounded Theory on 150 conversation traces from 5 open-source multi-agent systems. [arXiv](https://arxiv.org/abs/2503.13657) |
| **R-Judge (Yuan et al.)** | EMNLP Findings 2024 / ICLR 2024 | Benchmark for LLM agent *safety risk awareness*: 569 multi-turn records, 27 risk scenarios. Best model (GPT-4o) only achieves 74.42%. [arXiv](https://arxiv.org/abs/2401.10019) |
| **AgentHarm** | ICLR 2025 | Benchmark for agent resistance to harmful tasks. Even frontier models show 48-85% refusal rates with significant compliance in remainder. [ICLR 2025 Proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/file/c493d23af93118975cdbc32cbe7323f5-Paper-Conference.pdf) |

### 2.3 Abstention Benchmarks and Methods (2025)

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| **AbstentionBench (Kirichenko et al., Meta)** | NeurIPS 2025 D&B Track | 20-dataset benchmark. **Critical finding: reasoning fine-tuning DEGRADES abstention by 24% on average**, even in domains where reasoning models excel. Scaling provides little benefit. [arXiv](https://arxiv.org/abs/2506.09038) |
| **"Improving LLM Reliability through Hybrid Abstention and Adaptive Detection" (Sharma et al.)** | arXiv 2025 (2602.15391) | Proposes adaptive thresholds that adjust based on domain sensitivity and user trust signals. Multi-dimensional detection with hierarchical cascade. Directly relevant to the external enforcement thesis. [arXiv](https://arxiv.org/abs/2602.15391) |
| **"Trust or Escalate: LLM Judges with Provable Guarantees"** | ICLR 2025 (Oral) | Cascaded selective evaluation: start with cheap model, escalate to stronger model when confidence is low. Provides **provable guarantees** of human agreement. Demonstrates external escalation > internal confidence alone. [ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf) |

### 2.4 Step-Level Verification (Process Reward Models)

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| **Lightman et al., "Let's Verify Step by Step"** | ICLR 2024 (OpenAI) | Process supervision significantly outperforms outcome supervision. PRM800K dataset with 800K step-level labels. Directly relevant to external verification of agent reasoning. [arXiv](https://arxiv.org/abs/2305.20050) |
| **Varshney et al., "A Stitch in Time Saves Nine"** | arXiv 2023 | Detects hallucinations *during generation* via logit confidence, validates with external checks, mitigates before continuing. Reduces GPT-3.5 hallucinations from 47.5% to 14.5%. [arXiv](https://arxiv.org/abs/2307.03987) |

### 2.5 Multi-Agent Approaches

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| **Du et al., "Improving Factuality and Reasoning through Multiagent Debate"** | ICML 2024 | Multiple LLM instances debate responses over rounds. Reduces hallucinations. But: agents can share blind spots (correlated errors), debate can increase confidence without truth. [arXiv](https://arxiv.org/abs/2305.14325) |

### 2.6 Runtime Guardrails (Engineering Frameworks)

| System | Key Relevance |
|--------|--------------|
| **NeMo Guardrails (NVIDIA)** | Open-source toolkit for programmable runtime guardrails. Implements input/output rails, dialog rails, retrieval rails, execution rails. Represents the "external enforcement" approach in production. [GitHub](https://github.com/NVIDIA-NeMo/Guardrails) |
| **Guardrails AI** | Schema validation + structural enforcement for LLM outputs |

---

## SECTION 3: ASSESSMENT OF THESIS POSITIONING

### 3.1 Claim: "External enforcement beats internal confidence"

**Literature Support: MODERATE TO STRONG, with important nuances**

**Evidence FOR the thesis:**

1. **Xiong et al. (ICLR 2024)** directly demonstrates that LLMs are overconfident when self-reporting uncertainty. Internal confidence is unreliable.

2. **AbstentionBench (NeurIPS 2025)** shows that reasoning fine-tuning *degrades* abstention ability by 24%. Internal improvements to reasoning do not translate to better knowing-when-to-stop.

3. **Lightman et al. (ICLR 2024)** demonstrates that external process supervision outperforms outcome supervision (and implicitly, self-assessment) for step verification.

4. **"Trust or Escalate" (ICLR 2025, Oral)** provides a formal framework where external escalation with provable guarantees outperforms single-model confidence-based judgment.

5. **SelfCheckGPT's own limitation**: correlated hallucinations (model consistently wrong) defeat consistency-based self-checks, demonstrating a fundamental ceiling on internal methods.

6. **"How Do LLMs Fail In Agentic Scenarios?"** shows that model scale does not predict agentic robustness -- the internal capabilities do not automatically transfer to reliable agent behavior.

**Evidence AGAINST or COMPLICATING the thesis:**

1. **Kadavath et al. (2022)** shows models *do* contain meaningful self-knowledge signals. P(IK) is useful. The question is not whether internal signals exist but whether they are *sufficient*.

2. **Tian et al. (EMNLP 2023)** found that verbalized confidence is *better calibrated* than token probabilities after RLHF. This suggests internal methods can improve.

3. **Kuhn et al. (ICLR 2023)** semantic entropy is an *internal* method that significantly outperforms baselines. Pure internal UQ is not hopeless.

4. **The dichotomy itself may be false**: The most effective approaches in practice are **hybrid** -- combining internal signals with external verification. The "Hybrid Abstention and Adaptive Detection" paper (2025) explicitly proposes this. NeMo Guardrails combines LLM self-checking with external policy rails.

5. **Wen et al. (TACL 2025)** frames abstention along three axes (query/model/values), not a simple internal/external binary. The survey does not conclude that one approach dominates.

### 3.2 Recommended Positioning Refinement

Instead of "external enforcement beats internal confidence," the literature better supports:

> **"Internal confidence signals are necessary but insufficient for reliable agent abstention. External enforcement mechanisms provide critical complementary guarantees, especially under distribution shift, in high-stakes domains, and for multi-step agentic workflows where errors compound."**

This is supported by:
- Internal signals exist (Kadavath) but are overconfident (Xiong) and degrade with reasoning training (AbstentionBench)
- External verification provides provable guarantees (Trust or Escalate) and catches errors internal methods miss (PRMs, SelfCheck limitations)
- Hybrid approaches are the emerging consensus (Sharma 2025, NeMo Guardrails, cascaded evaluation)

---

## SECTION 4: CONTRADICTING EVIDENCE AND ALTERNATIVE APPROACHES

### 4.1 Internal Methods That Work Well

- **Semantic entropy** (Kuhn et al.) provides strong uncertainty estimates from internal signals alone
- **Verbalized confidence** (Tian et al.) can be surprisingly well-calibrated after RLHF
- **Self-consistency / majority voting** (Wang et al., 2022) remains a strong baseline for reducing errors without external systems
- **Conformal prediction for LLMs** (multiple 2024 papers) provides statistical coverage guarantees using only model outputs

### 4.2 Approaches That Sidestep the Internal/External Debate

1. **RAG + answerability classifiers**: Ground generation in retrieved evidence; refuse when evidence is insufficient. Neither purely internal nor external in the abstention sense.

2. **Constrained decoding / structured outputs**: Prevent invalid actions at the decoding level. A form of external enforcement that operates at a different level than confidence.

3. **Constitutional AI / RLHF for honesty**: Train models to internalize refusal behavior. Blurs the line between internal and external (external constitution -> internalized behavior).

4. **Multi-agent debate** (Du et al., ICML 2024): Uses multiple internal models to approximate external verification. Effective but shares blind spots.

5. **Process reward models**: External verification of reasoning steps. Strong evidence for this approach in math/code; less clear for open-domain factuality.

### 4.3 Key Counterarguments the Thesis Must Address

1. **Cost/latency**: External enforcement adds computational overhead. For real-time agents, this trade-off matters.

2. **Specification problem**: External enforcement requires knowing *what to enforce*. For open-ended agent tasks, specifying correct behavior is as hard as the original problem.

3. **Quis custodiet ipsos custodes?**: External monitors can themselves be LLMs that hallucinate. "LLM-as-judge" approaches inherit the same fundamental limitations.

4. **The gap between QA abstention and agent stopping**: Most abstention research studies single-turn QA. Multi-step agent workflows have compounding error dynamics that are qualitatively different. The thesis should clearly delineate this gap.

---

## SECTION 5: OVERALL ASSESSMENT

### Academic Grounding: MOSTLY SOLID with corrections needed

**Strengths:**
- The three cited papers are all real, published in legitimate venues
- The topic is timely and the research area is active (2024-2025)
- The general direction (external enforcement matters) has growing support

**Required Corrections:**
1. **AUCM is NOT "Area Under the Coverage-Merit curve."** It stands for "Answerable-Unanswerable Confusion Matrix." This must be fixed -- it is a factual mischaracterization of the cited paper's contribution.

**Significant Gaps in References:**
1. Missing Kadavath et al. (2022) -- the foundational work on LLM self-knowledge
2. Missing Kuhn et al. (ICLR 2023) -- semantic entropy, the strongest internal UQ method
3. Missing Xiong et al. (ICLR 2024) -- directly supports the thesis (LLMs are overconfident)
4. Missing AbstentionBench (NeurIPS 2025) -- strongest evidence that internal approaches fail
5. Missing Lightman et al. (ICLR 2024) -- PRMs as external verification
6. Missing "Trust or Escalate" (ICLR 2025) -- external escalation with provable guarantees
7. Missing agent failure mode papers (2024-2025) -- grounds the problem empirically
8. Missing Tian et al. (EMNLP 2023) -- important counterpoint showing internal methods can work

**Positioning Risk:**
- The binary "external beats internal" framing is an oversimplification that will invite criticism
- The literature supports a **hybrid/complementary** framing more robustly
- The thesis should explicitly address the distinction between single-turn abstention (well-studied) and multi-step agent stopping (under-studied), positioning the contribution in the latter space

---

## APPENDIX: COMPLETE REFERENCE LIST FOR THESIS

### Must-Cite (Core)
1. Madhusudhan et al. (2024). "Do LLMs Know When to NOT Answer?" COLING 2025.
2. Wen et al. (2025). "Know Your Limits: A Survey of Abstention in LLMs." TACL 13:529-556.
3. Manakul et al. (2023). "SelfCheckGPT." EMNLP 2023.
4. Kadavath et al. (2022). "Language Models (Mostly) Know What They Know." arXiv.
5. Kuhn et al. (2023). "Semantic Uncertainty." ICLR 2023.

### Must-Cite (Supporting Thesis Direction)
6. Xiong et al. (2024). "Can LLMs Express Their Uncertainty?" ICLR 2024.
7. Kirichenko et al. (2025). "AbstentionBench." NeurIPS 2025.
8. Lightman et al. (2023). "Let's Verify Step by Step." ICLR 2024.
9. "Trust or Escalate" (2025). ICLR 2025.

### Should-Cite (Context and Balance)
10. Tian et al. (2023). "Just Ask for Calibration." EMNLP 2023.
11. Du et al. (2023). "Improving Factuality through Multiagent Debate." ICML 2024.
12. Varshney et al. (2023). "A Stitch in Time Saves Nine." arXiv.
13. "How Do LLMs Fail In Agentic Scenarios?" (2024). arXiv.
14. Cemri et al. (2025). "Why Do Multi-Agent LLM Systems Fail?" arXiv.
15. R-Judge (Yuan et al., 2024). EMNLP Findings 2024.
16. Sharma et al. (2025). "Hybrid Abstention and Adaptive Detection." arXiv.
