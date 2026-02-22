# Design: Agent Runtime Failure Mode Harness

## High-level architecture

AFL is a small state machine implemented via agent runtime hooks:

```
User Prompt ──► (UserPromptSubmit) ──► [maybe activate Failure Mode]
     │
     ├─► Tool call succeeds ─────────► normal flow
     │
     └─► Tool call fails ─► (PostToolUseFailure) ─► activate Failure Mode

Final assistant message ─► (Stop) ─► enforce template or block completion
```

The key property is that **enforcement is external**:
- the Stop hook inspects the final assistant message and blocks completion until it matches a required template.

This design targets multi-step agentic workflows, not single-turn question answering. In a multi-step context, errors compound across tool calls: the agent can bluff about actions it did not take, and downstream steps build on that fabricated state. The hooks intercept at each boundary where that compounding can occur.

## Hook roles

### 1) UserPromptSubmit (preflight)
File: `hooks/afl_user_prompt.py`

Purpose:
- Catch prompts that are likely **unverifiable** (exact future predictions, guaranteed outcomes)
- Catch prompts that are likely **under-specified** ("fix the bug" with no repro/logs)
- Activate Failure Mode state early and inject `additionalContext`

This is heuristic. The hard guarantee is the Stop gate.

### 2) PostToolUseFailure
File: `hooks/afl_post_tool_failure.py`

Purpose:
- If a tool fails, force the agent into Failure Mode so it cannot "pretend success".
- Inject context: "do NOT claim success; propose recovery steps".

### 3) Stop gate
File: `hooks/afl_stop_gate.py`

Purpose:
- If Failure Mode state is active, require the assistant response to contain:
  - `FAILURE MODE`
  - `Status:`
  - `Blocked because:`
  - `To proceed I need:`
  - `Safe next actions (I can do now):`

If missing, Stop hook blocks completion up to `maxStopBlocks` times, then fails open to avoid deadlock.

### Status taxonomy

The `Status:` field in a Failure Mode response must be one of the following values:

| Status | Meaning |
|---|---|
| `NEEDS_INFO` | The agent lacks required input (repro steps, logs, constraints) to proceed safely. |
| `NEEDS_PERMISSION` | The action is within scope but requires explicit user authorization before execution. |
| `BLOCKED_BY_POLICY` | A configured policy rule (deny list, PreToolUse guard) prohibits the requested operation. |
| `CANNOT_VERIFY` | The request asks for an outcome the agent cannot confirm or falsify (future predictions, hidden state). |

#### Future status candidates

The following codes are under consideration for v4 but are not yet implemented:

- `LOOP_DETECTED` — the agent recognizes it is repeating the same failed approach; would require tracking action history across hook invocations.
- `BUDGET_EXCEEDED` — a resource limit has been hit (token count, tool call count, or wall time); requires the runtime to expose consumption metrics to hooks.
- `TOOL_UNAVAILABLE` — a required capability (e.g., a specific MCP tool, a file path, a network endpoint) does not exist in the current environment.

### Optional hooks
- `PreToolUse` (`hooks/afl_pre_tool.py`): deny/ask lists for commands/paths.
- `TaskCompleted` (`hooks/afl_task_completed.py`): run tests and block completion on failure (exit code 2).

## Policy file

File: `afl_policy.json`

Key sections:
- `features`: turn hooks on/off without uninstalling them
- `promptFailTriggers`: regex triggers for `cannotVerify` and `needsInfo`
- `requiredFailureModeHeadings`: patterns enforced by Stop gate
- `denyPathRegex`, `denyBashRegex`, `askBashRegex`: (optional) PreToolUse policies
- `taskCompleted`: test command / auto-detection config

## State storage

AFL stores a small JSON state file indicating whether Failure Mode is active.

Design goal: **do not create `.claude/` inside repos unless it already exists.**

- If `<project>/.claude/` exists:
  - state is stored in `<project>/.claude/state/afl_state.json`
- Else:
  - state is stored globally under:
    `~/.claude/afl_state/<project-key>/afl_state.json`

This prevents accidental repo pollution while keeping state scoped per project.

## Hook composition (important)

The agent runtime can run multiple matching hooks "in parallel". If you already have global `PreToolUse` blockers, enabling AFL's own `PreToolUse` may create conflicts or surprising outcomes.

Recommendation:
- Start with **minimal install** (UserPromptSubmit + PostToolUseFailure + Stop).
- Enable `PreToolUse` only if you do not already have equivalent guards.
- Treat policy as code: test before enabling in a high-stakes repo.

See `05-limitations.md` for failure cases.
