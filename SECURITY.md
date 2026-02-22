# Security Policy

## Scope

AFL (Agent Failure Mode) is a local harness for the agent runtime. It can affect:
- which commands the agent attempts to run
- whether the agent is allowed to "complete" a task
- how the agent is instructed to respond when uncertain

It does **not** provide sandboxing. It is not a substitute for:
- OS permissions
- container isolation
- least-privilege credentials
- code review

## Reporting a vulnerability

If you believe you've found a security issue (e.g., policy bypass, unexpected command execution),
please open a GitHub issue labeled **security** and include:

- your OS + agent runtime version
- your `afl_policy.json` (redacted)
- minimal reproduction steps

If it's sensitive, avoid posting secrets and instead provide a redacted version.

## Threat model (what we try to prevent)

- "Bluffing" about tool execution (claiming tests ran when they didn't)
- Proceeding on under-specified tasks without asking for missing inputs
- Irreversible actions without explicit permission (optional feature via PreToolUse)

## Non-goals

- Preventing all hallucinations
- Defending against a fully malicious local user
- OS-level isolation or endpoint security
