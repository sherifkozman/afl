# HaluEval Benchmark: Comprehensive Analysis for AFL Integration

## Executive Summary

HaluEval is a large-scale hallucination evaluation benchmark containing 35,000 samples across four tasks (QA, dialogue, summarization, and general user queries). It was published at EMNLP 2023 by Li et al. from Renmin University of China. The benchmark's standard evaluation protocol tests whether LLMs can *detect* hallucinations in given responses -- a classification task. Adapting it for AFL (which *prevents* hallucination via structured abstention) requires reframing: instead of classifying existing responses, AFL would generate responses to the same prompts and be measured on whether it abstains when hallucination would occur. The QA and summarization splits are best suited for this; the general split is problematic due to open-ended nature and lack of grounding context.

---

## 1. Dataset Structure

### 1.1 Overview

| Config | Rows | Source Seed Data | Format |
|--------|------|-----------------|--------|
| `qa` (paired) | 10,000 | HotpotQA | Parquet (HF) / JSON (GitHub) |
| `qa_samples` | 10,000 | HotpotQA | Parquet / JSONL |
| `dialogue` (paired) | 10,000 | OpenDialKG | Parquet / JSON |
| `dialogue_samples` | 10,000 | OpenDialKG | Parquet / JSONL |
| `summarization` (paired) | 10,000 | CNN/Daily Mail | Parquet / JSON |
| `summarization_samples` | 10,000 | CNN/Daily Mail | Parquet / JSONL |
| `general` | 4,507 | Alpaca (52K instructions) | Parquet / JSON |
| **Total** | **64,507** (with overlap between paired/samples) | | |

**Note:** The "paired" and "samples" versions contain the SAME underlying data in different formats. The paired version has both `right_answer` and `hallucinated_answer` per row. The samples version flattens this into individual rows with a binary `hallucination` label. The core unique data is 30,000 task-specific + ~5,000 general = ~35,000 examples.

### 1.2 Exact Fields Per Config

**QA (paired)** -- `qa` config:
```json
{
  "knowledge": "Arthur's Magazine (1844-1846) was an American literary periodical...",
  "question": "Which magazine was started first Arthur's Magazine or First for Women?",
  "right_answer": "Arthur's Magazine",
  "hallucinated_answer": "First for Women was started first."
}
```

**QA (samples)** -- `qa_samples` config:
```json
{
  "knowledge": "Arthur's Magazine (1844-1846) was an American literary periodical...",
  "question": "Which magazine was started first Arthur's Magazine or First for Women?",
  "answer": "First for Women was started first.",
  "hallucination": "yes"
}
```

**Dialogue (paired)** -- `dialogue` config:
```json
{
  "knowledge": "Iron Man is starring Robert Downey Jr. ...",
  "dialogue_history": "[Human]: Do you like Iron Man [Assistant]: Sure do! ...",
  "right_response": "I like crime fiction! Didn't know RDJ was in there. Jake Gyllenhaal starred as well.",
  "hallucinated_response": "I'm not a fan of crime movies, but I did know that RDJ starred in Zodiac with Tom Hanks."
}
```

**Dialogue (samples)** -- `dialogue_samples` config:
```json
{
  "knowledge": "...",
  "dialogue_history": "...",
  "response": "...",
  "hallucination": "yes"
}
```

**Summarization (paired)** -- `summarization` config:
```json
{
  "document": "Marseille, France (CNN) The French prosecutor leading an investigation...",
  "right_summary": "Marseille prosecutor says 'so far no videos were used in the crash investigation'...",
  "hallucinated_summary": "A video showing the final moments of Germanwings Flight 9525 has been recovered..."
}
```

**Summarization (samples)** -- `summarization_samples` config:
```json
{
  "document": "...",
  "summary": "...",
  "hallucination": "yes"
}
```

**General** -- `general` config:
```json
{
  "ID": "1",
  "user_query": "Produce a list of common words in the English language.",
  "chatgpt_response": "the, a, and, to, in, that, is, it...",
  "hallucination": "no",
  "hallucination_spans": []
}
```
When `hallucination` is `"yes"`, `hallucination_spans` contains the specific text spans identified as hallucinated (802 of 4,507 examples have non-empty spans).

### 1.3 Label Distribution

| Config | `hallucination=yes` | `hallucination=no` | Total |
|--------|--------------------:|-------------------:|------:|
| `qa_samples` | 5,010 (50.1%) | 4,990 (49.9%) | 10,000 |
| `dialogue_samples` | 5,010 (50.1%) | 4,990 (49.9%) | 10,000 |
| `summarization_samples` | 5,010 (50.1%) | 4,990 (49.9%) | 10,000 |
| `general` | 815 (18.1%) | 3,692 (81.9%) | 4,507 |

The task-specific samples are near-perfectly balanced. The general split is heavily skewed toward non-hallucinated (consistent with the paper's 19.5% figure -- see Section 2).

### 1.4 Dataset Size

| Config | Characters | ~Tokens (chars/4) |
|--------|----------:|---------:|
| `qa` | 5,305,537 | 1,326,385 |
| `qa_samples` | 4,931,706 | 1,232,927 |
| `dialogue` | 6,048,870 | 1,512,218 |
| `dialogue_samples` | 5,140,147 | 1,285,037 |
| `summarization` | 46,147,660 | 11,536,915 |
| `summarization_samples` | 42,486,049 | 10,621,513 |
| `general` | 2,809,655 | 702,414 |
| **Total** | **112,869,624** | **~28.2M** |

The summarization split dominates size because it includes full CNN/Daily Mail documents.

---

## 2. How Hallucination Is Defined and Labeled

### 2.1 Definition

The paper defines hallucination as "content that conflicts with the source or cannot be verified by the factual knowledge." This covers:

- **Input-conflicting hallucination**: output contradicts the provided context/knowledge
- **Fact-conflicting hallucination**: output contradicts established world knowledge
- **Unverifiable information**: output fabricates details that cannot be verified

### 2.2 Label Creation

**Task-specific splits (QA, dialogue, summarization):**
- Labels are **automatically generated** via ChatGPT using a **sampling-then-filtering** pipeline
- Step 1: Given a seed example from HotpotQA/OpenDialKG/CNN-DM, ChatGPT generates hallucinated counterparts using two methods:
  - **One-pass**: complete instruction fed to ChatGPT, single-shot generation
  - **Conversational**: multi-turn teaching where ChatGPT learns to generate hallucinations step by step
- Step 2: A filtering step selects the most "plausible and difficult" hallucinated sample using ChatGPT as a judge with ground-truth examples
- The `right_answer`/`right_response`/`right_summary` comes directly from the original dataset
- Labels are therefore **structurally determined** -- if the answer came from the hallucinated generation pipeline, it is labeled `yes`; if from the original dataset, `no`

**General split:**
- 5,000 user queries sampled from Alpaca's 52K instruction dataset
- ChatGPT sampled 3 responses per query; queries with low-similarity responses were retained (indicating potential hallucination)
- **Human annotators** labeled whether each response is hallucinated
- Max-voting strategy across multiple annotators for final label
- Annotators also marked **hallucination spans** (specific text segments)
- Result: 977/5,007 responses labeled as hallucinated (**19.5%**)
- The published dataset has 4,507 examples (likely after filtering); 815 labeled `yes` (18.1%)

### 2.3 Label Format

- **Binary**: `"yes"` or `"no"` (string, not boolean)
- In the `general` split, additionally provides `hallucination_spans` (list of strings)
- No continuous scores or confidence levels

### 2.4 Hallucination Patterns (from the paper)

The paper defines task-specific hallucination patterns:

| Task | Pattern I | Pattern II | Pattern III | Pattern IV |
|------|-----------|------------|-------------|------------|
| QA | Comprehension (factually correct but context-conflicting) | Factuality (fabricated facts) | Specificity (wrong level of detail) | Inference (wrong logical inference) |
| Dialogue | Extrinsic-Soft (entity replaced with similar entity) | Extrinsic-Hard (entity replaced with dissimilar entity) | Extrinsic-Type (entity replaced with different type) | -- |
| Summarization | Factual (non-entailed from document) | Non-factual (contradicts document) | Intrinsic (misrepresents document content) | -- |

---

## 3. Standard Evaluation Protocol

### 3.1 Task Framing

The standard HaluEval evaluation is a **binary classification** task:
- For each example, randomly select either the `right_answer` or `hallucinated_answer`
- Present the input (question/dialogue/document) + selected answer to the model
- Ask the model: "Does this contain hallucination? Yes/No"
- Compare model output to ground truth

This is a **detection** task, not a generation task.

### 3.2 Evaluation Prompts (Exact Templates)

The repo contains three instruction files used as system/user prompts. Each includes:

**QA evaluation prompt** (system): "You are a hallucination detector. You MUST determine if the provided answer contains hallucination or not for the question based on the world knowledge."

The user instruction includes few-shot examples covering four hallucination patterns:
1. Context misunderstanding
2. Factual contradiction / fabrication
3. Specificity errors
4. Inference errors

Format: `#Question#: {question}\n#Answer#: {answer}\n#Your Judgement#:`

**Dialogue evaluation prompt** (system): "You are a response judge. You MUST determine if the provided response contains non-factual or hallucinated information."

Few-shot examples cover entity replacement patterns (similar, dissimilar, wrong-type).

Format: `#Dialogue History#: {dialog}\n#Response#: {response}\n#Your Judgement#:`

**Summarization evaluation prompt** (system): "You are a summary judge. You MUST determine if the provided summary contains non-factual or hallucinated information."

Few-shot examples cover non-entailment, factual errors, and contradictions.

Format: `#Document#: {document}\n#Summary#: {summary}\n#Your Judgement#:`

### 3.3 Metric

**Accuracy** is the primary (and only standard) metric: percentage of correct Yes/No classifications. No F1, AUROC, or precision/recall are reported in the original paper.

### 3.4 Baseline Results (Table 5 from paper)

Accuracy (%) of classifying whether a sample contains hallucinated contents:

| Model | QA | Dialogue | Summarization | General |
|-------|---:|--------:|--------------:|--------:|
| ChatGPT (gpt-3.5-turbo) | 62.59 | 72.40 | 58.53 | 86.22* |
| Claude 2 | 69.78 | 64.73 | 57.75 | 79.44 |
| Claude | 67.60 | 64.83 | 53.76 | 75.00 |
| Davinci-002 | 60.05 | 60.81 | 47.77 | 80.42 |
| Davinci-003 | 49.65 | 68.37 | 48.07 | 80.40 |
| GPT-3 (Davinci) | 49.21 | 50.02 | 51.23 | 72.72 |
| Llama 2 (7B) | 49.60 | 43.99 | 49.55 | 20.46 |
| ChatGLM (7B) | 47.93 | 44.41 | 48.57 | 30.92 |
| Falcon (7B) | 39.66 | 29.08 | 42.71 | 18.98 |
| Vicuna (7B) | 60.34 | 46.35 | 45.62 | 19.48 |
| Alpaca (7B) | 6.68 | 17.55 | 20.63 | 9.54 |

*Note: The 86.22 for ChatGPT on General appears in Table 8 (the value in Table 5 description text shows 79.44 for Claude 2 on General). Some table cells in the paper's markdown rendering are misaligned; the numbers above are the best reconstruction from the scraped paper.

### 3.5 Improvement Strategy Results (Table 8 from paper)

ChatGPT accuracy with different strategies:

| Strategy | QA | Dialogue | Summarization | General |
|----------|---:|--------:|--------------:|--------:|
| Baseline (ChatGPT) | 62.59 | 72.40 | 58.53 | 86.22 |
| + Knowledge Retrieval | **76.83** | **73.80** | -- | **90.73** |
| + Chain-of-Thought | 59.58 | 71.39 | **61.21** | 86.50 |
| + Sample Contrast | 49.19 | 68.67 | 49.46 | -- |

Key findings:
- Knowledge retrieval dramatically helps QA (+14.24 points) and general (+4.51)
- CoT actually *hurts* QA (-3.01) and dialogue (-1.01) but helps summarization (+2.68)
- Sample contrast (providing ground truth for comparison) performs *worst*, suggesting the hallucinated samples are very plausible

### 3.6 ChatGPT Failure Analysis (Table 6)

Number of samples where ChatGPT fails to recognize hallucination, by pattern:

| Task | Total Failed | P-I | P-II | P-III | P-IV |
|------|----------:|----:|-----:|------:|-----:|
| QA | 3,109 | 1,559 | 245 | 278 | 1,027 |
| Dialogue | 891 | 465 | 344 | 82 | -- |
| Summarization | 3,868 | 3,106 | 705 | 57 | -- |

Over half of failures come from Pattern I (factually correct but context-conflicting), indicating LLMs struggle most when hallucinations are plausible.

---

## 4. Access and Hosting

### 4.1 Primary Sources

| Resource | URL |
|----------|-----|
| Paper (arXiv) | https://arxiv.org/abs/2305.11747 |
| Paper (ACL Anthology) | https://aclanthology.org/2023.emnlp-main.397.pdf |
| GitHub (official) | https://github.com/RUCAIBox/HaluEval |
| HuggingFace (primary mirror) | https://huggingface.co/datasets/pminervini/HaluEval |
| HuggingFace (alternative) | https://huggingface.co/datasets/flowaicom/HaluEval |

### 4.2 Citation

```bibtex
@inproceedings{li2023halueval,
  title={HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models},
  author={Li, Junyi and Cheng, Xiaoxue and Zhao, Wayne Xin and Nie, Jian-Yun and Wen, Ji-Rong},
  booktitle={Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  year={2023}
}
```

**Venue**: EMNLP 2023 Main Conference (Long Paper)

### 4.3 License

- GitHub repository: **MIT License**
- HuggingFace (pminervini): **Apache 2.0**
- No access restrictions; freely downloadable

### 4.4 Loading Code

```python
from datasets import load_dataset

# Paired format (right + hallucinated)
qa_paired = load_dataset("pminervini/HaluEval", "qa", split="data")
dialogue_paired = load_dataset("pminervini/HaluEval", "dialogue", split="data")
summarization_paired = load_dataset("pminervini/HaluEval", "summarization", split="data")

# Samples format (single answer + label)
qa_samples = load_dataset("pminervini/HaluEval", "qa_samples", split="data")
dialogue_samples = load_dataset("pminervini/HaluEval", "dialogue_samples", split="data")
summarization_samples = load_dataset("pminervini/HaluEval", "summarization_samples", split="data")

# General (human-annotated)
general = load_dataset("pminervini/HaluEval", "general", split="data")
```

---

## 5. Adaptation for AFL

### 5.1 The Fundamental Reframing

HaluEval's standard protocol asks: "Given a response, is it hallucinated?"
AFL's question is: "Given a prompt, does the agent abstain instead of hallucinating?"

This requires flipping from **post-hoc detection** to **generation-time prevention**.

### 5.2 Proposed AFL Evaluation Protocol

**For each HaluEval example:**

1. Extract the input prompt (question + knowledge for QA, dialogue_history + knowledge for dialogue, document for summarization)
2. Present this to the AFL-equipped agent as a natural query
3. The agent either:
   - (a) Produces a substantive answer, OR
   - (b) Triggers the AFL failure template (structured abstention)
4. Score the output:
   - If the example has a hallucinated answer that is "plausible" (i.e., it was generated as hallucination-inducing), and the agent abstains --> **true positive** (correct abstention)
   - If the example has a right answer available and the agent answers correctly --> **true negative** (correct response)
   - If the agent hallucinate where it should abstain --> **false negative** (missed hallucination)
   - If the agent abstains where it could answer correctly --> **false positive** (over-refusal)

**But there is a critical problem**: HaluEval examples all have correct answers. The questions are answerable. The hallucination in HaluEval comes from the *model generating wrong content*, not from the questions being *unanswerable*. An agent with good knowledge would answer correctly rather than abstain.

### 5.3 Better Reframing: Counterfactual Generation Test

A more workable approach:

1. For each paired example, present the prompt to the AFL agent
2. Compare the agent's output against both `right_answer` and `hallucinated_answer`
3. Measure:
   - **Correctness rate**: How often does the agent's answer match the right answer?
   - **Hallucination rate**: How often does the agent's answer resemble the hallucinated answer?
   - **Abstention rate**: How often does the agent trigger the failure template?
   - **Appropriate abstention**: Of the cases where the agent would have hallucinated (matched the hallucinated pattern), how many did it catch and abstain?

### 5.4 Split Suitability for AFL

| Split | Suitability | Reasoning |
|-------|-------------|-----------|
| **QA** | **HIGH** | Clear right/wrong answers, grounding knowledge provided, easy to verify correctness. If AFL detects it lacks sufficient knowledge to answer, abstention is appropriate. The knowledge field can be withheld/modified to create scenarios requiring abstention. |
| **Summarization** | **HIGH** | Document is provided as grounding context. Hallucination = unsupported by document. AFL can check whether its summary is entailed by the document. Source document can be used for verification. |
| **Dialogue** | **MEDIUM** | Knowledge-grounded dialogue with clear factual grounding. However, dialogue responses are more open-ended and harder to verify mechanically. Entity substitution hallucinations may not trigger AFL's failure mode. |
| **General** | **LOW** | Open-ended queries without grounding context. No clear "right answer" to compare against. Abstention would be over-broad (many queries are subjective/creative). The human-annotated hallucination spans are useful for analysis but the open-ended nature makes AFL evaluation ambiguous. |

### 5.5 Recommended AFL Evaluation Design

**Phase 1: Knowledge Withholding Test (QA split)**
- Take QA examples and present ONLY the question (withhold the `knowledge` field)
- If the agent lacks the knowledge to answer correctly, AFL should trigger
- Measure: abstention rate on questions the agent cannot answer vs. accuracy on questions it can
- This creates a natural "answerable vs. unanswerable" split based on the agent's actual knowledge

**Phase 2: Faithfulness Test (Summarization split)**
- Present document + summarization request
- Check if the agent's summary is faithful to the document
- AFL should prevent generation of content not entailed by the document
- Measure: faithfulness of non-abstained summaries vs. abstention rate

**Phase 3: Knowledge-Grounded Dialogue Test**
- Present dialogue history + knowledge context
- Check if responses are faithful to provided knowledge
- AFL should catch when the agent would fabricate entities

### 5.6 Metrics for AFL on HaluEval

Primary metrics:
- **Risk-Coverage Curve**: Plot hallucination rate (risk) vs. coverage (fraction of queries answered)
- **AURC** (Area Under Risk-Coverage curve): Single summary number; lower is better
- **Selective Accuracy**: Accuracy on queries where the agent chose to answer
- **Abstention Precision**: Of abstentions, what fraction would have been hallucinations?
- **Over-Refusal Rate**: Fraction of answerable queries incorrectly abstained on

Composite:
```
Utility = Accuracy_on_answered - lambda1 * Hallucination_rate - lambda2 * Over_refusal_rate
```

---

## 6. Related Work

### 6.1 Abstention/Refusal on HaluEval

**Direct evaluations of abstention protocols against HaluEval are rare.** The benchmark was designed for detection (classify existing responses), not for evaluating generation-time abstention. Most abstention/selective prediction work uses other benchmarks.

### 6.2 Relevant Papers

| Paper | Year | Venue | Relevance |
|-------|------|-------|-----------|
| Li et al., "HaluEval" | 2023 | EMNLP | The original benchmark |
| Li et al., "The Dawn After the Dark" | 2024 | arXiv (2401.03205) | Same authors; empirical study on factuality hallucination in LLMs |
| Zhu et al., "HaluEval-Wild" | 2024 | arXiv (2403.04307) | Extension to in-the-wild hallucination evaluation |
| Lamba et al., "Investigating Symbolic Triggers" | 2025 | arXiv (2509.09715) | Tests Gemma models on HaluEval + TruthfulQA |
| Lamba et al., "SymLoc" | 2025 | arXiv (2511.14172) | Symbolic localization of hallucination across HaluEval + TruthfulQA |
| Lin, Hilton & Evans, "TruthfulQA" | 2022 | ACL | Closer to abstention evaluation; questions designed to elicit plausible falsehoods |
| Geifman & El-Yaniv, "Selective Classification" | 2017 | NeurIPS | Foundational theory for risk-coverage / selective prediction |
| Rajpurkar et al., "SQuAD 2.0" | 2018 | ACL | Unanswerable questions; classic abstention benchmark |
| Thorne et al., "FEVER" | 2018 | NAACL | "NOT ENOUGH INFO" label = natural abstention target |

### 6.3 Better Benchmarks for Abstention Testing

For pure abstention/refusal evaluation, these may be more directly suitable than HaluEval:

- **TruthfulQA**: Questions designed to elicit plausible falsehoods; "I don't know" is a valid answer
- **SQuAD 2.0**: Explicit unanswerable questions mixed with answerable ones
- **FEVER (NEI subset)**: "Not Enough Info" is a first-class label
- **Natural Questions (unanswerable subset)**: Some questions have no answer in the provided document

**However**, HaluEval has unique value for AFL because:
1. It tests across multiple task types (QA, dialogue, summarization), not just QA
2. The hallucinated samples are generated to be *plausible*, testing whether AFL catches subtle errors
3. The grounding context (knowledge fields) enables faithful-to-context evaluation

### 6.4 Abstention Approaches in Literature

| Approach | How It Works | AFL Comparison |
|----------|-------------|----------------|
| Confidence thresholding | Abstain when logprob/entropy exceeds threshold | AFL uses structural rules, not probabilities |
| Instruction-based ("If unsure, say IDK") | Soft prompt instruction | AFL uses hard-coded failure templates |
| Verifier-gated | Generate then fact-check, abstain if verification fails | AFL prevents generation, does not verify post-hoc |
| Conformal prediction | Statistical coverage guarantees | Orthogonal; could complement AFL |
| RAG + cite-or-abstain | Abstain if no supporting retrieval | Closest to AFL philosophy |

---

## 7. Practical Considerations

### 7.1 Compute Requirements

- **Dataset loading**: Fast; ~500MB total on disk (dominated by summarization documents)
- **Evaluation**: Requires running the target model on 10,000-30,000 prompts per split
- **Cost estimate for API models**: At ~500 tokens per QA prompt, 10K examples = ~5M input tokens. At current GPT-4 rates (~$2.50/M input), that is approximately $12.50 per QA split evaluation run. Summarization is much more expensive due to long documents (~2,000 tokens each = ~20M tokens per split = ~$50).
- **GPU for open models**: A single run through 10K examples on a 7B model takes 2-4 hours on a single A100.

### 7.2 Known Issues and Limitations

1. **Contamination risk**: HaluEval samples are generated by ChatGPT. Models trained on ChatGPT outputs (or later versions of GPT) may have seen similar patterns in training data.

2. **ChatGPT-generated hallucinations**: The hallucinated samples were generated by ChatGPT, so they reflect ChatGPT's style of hallucination. Other models may hallucinate differently.

3. **Label noise in task-specific splits**: Labels are structurally determined (from pipeline), not human-verified. Some "hallucinated" answers may be partially correct, and some "right" answers may contain minor errors from the source datasets.

4. **General split size**: Only 4,507 examples with an imbalanced distribution (18.1% hallucinated). The human annotation provides higher quality but smaller quantity.

5. **Prompt sensitivity**: Results are highly sensitive to the evaluation prompt. The original paper's few-shot prompts are specific to their hallucination pattern taxonomy.

6. **No standard train/test split**: The dataset uses a single `data` split. There is no official train/validation/test partition, making it harder to prevent overfitting evaluation.

7. **Binary labels only**: No severity scores, confidence levels, or fine-grained hallucination type labels in the machine-readable format (though the paper discusses patterns qualitatively).

### 7.3 The `flowaicom/HaluEval` Alternative

This alternative HuggingFace mirror restructures the data with different fields:
```json
{
  "id": "halueval-0",
  "passage": "...",
  "question": "...",
  "answer": "...",
  "label": "FAIL",
  "source_ds": "halueval",
  "score": 0
}
```
Uses `FAIL`/`PASS` labels and a numeric `score` field. This may be more convenient for AFL integration since `FAIL` maps naturally to "this response is hallucinated; AFL should have caught it."

---

## 8. Recommended Next Steps for AFL Integration

1. **Start with QA paired split** (`pminervini/HaluEval`, config `qa`). It has clear grounding knowledge, verifiable answers, and structured hallucination patterns.

2. **Design two evaluation modes**:
   - **Mode A (Knowledge Available)**: Give AFL the question + knowledge context. Measure if AFL answers correctly or abstains when it should.
   - **Mode B (Knowledge Withheld)**: Give AFL only the question. Measure if AFL abstains on questions it cannot answer from parametric knowledge alone.

3. **Use the paired format**, not the samples format, to enable counterfactual analysis (compare agent output against both right and hallucinated answers).

4. **Report risk-coverage curves** rather than just accuracy, since AFL is fundamentally a selective prediction system.

5. **Benchmark against baselines**:
   - Vanilla model (no AFL)
   - Model + "If unsure, say I don't know" instruction
   - Model + AFL failure template
   - Model + RAG + AFL
