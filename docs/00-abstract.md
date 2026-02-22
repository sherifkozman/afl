# Abstract

Large Language Model (LLM) agents are optimized to be helpful and fluent. In practice this often means they **continue producing plausible output** when a task is under-specified, unverifiable, or blocked by missing access. The result is a familiar failure mode: **hallucination**, including "bluffing" about actions that did not occur (e.g., claiming tests ran).

AFL (Agent Failure Mode) implements a pragmatic countermeasure for the agent runtime: a **Failure Mode Harness** that can be installed globally or per-project. When the harness detects conditions where the agent cannot safely proceed, it forces a structured response template that:

1) states why progress is blocked,
2) requests the minimum missing information or permission, and
3) proposes safe next actions that do not require guessing.

Unlike single-turn abstention research (SelfCheckGPT, AbstentionBench), AFL targets **multi-step agentic workflows**, where errors compound across steps and bluffing about completed actions is a distinct failure class. The key concept is **typed terminal states**: when the harness fires, the agent must declare a structured stop reason (NEEDS_INFO, NEEDS_PERMISSION, BLOCKED_BY_POLICY, CANNOT_VERIFY) and specify what it needs to resume. No existing agent framework (LangChain, AutoGen, CrewAI) provides typed stop reasons — they use blunt iteration limits or string-matching termination with no enforceable protocol.

AFL does not treat internal model confidence as sufficient. Instead it relies on observable signals (prompt heuristics, tool failures, optional test gates) and **enforces compliance via the Stop hook**, preventing the agent from "finishing" until it follows the Failure Mode protocol.

See `01-thesis.md` for the argument, `02-design.md` for the state machine, and `04-testing.md` for evaluation.
