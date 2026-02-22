#!/usr/bin/env python3
"""UserPromptSubmit hook.

Core goal: catch prompts that are intrinsically unanswerable/unverifiable or
under-specified,
*before* the agent starts confidently guessing.

Strategy:
- Use policy.promptFailTriggers regex lists.
- If matched, activate failure mode state.
- Inject additionalContext so the agent is nudged into the FAILURE MODE template.

This is intentionally heuristic (not magic). The hard guarantee comes from Stop gate.
"""

from __future__ import annotations

import json

from afl_lib import (
    activate_state,
    feature_enabled,
    load_hook_input,
    load_policy,
    regex_list_match,
)


def main() -> None:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "userPromptSubmit"):
        return

    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return

    triggers = policy.get("promptFailTriggers") or {}
    cannot_verify = triggers.get("cannotVerify") or []
    needs_info = triggers.get("needsInfo") or []

    status = None
    reason = None

    if regex_list_match(cannot_verify, prompt):
        status = "CANNOT_VERIFY"
        reason = (
            "Prompt appears to request an exact, unverifiable outcome. "
            "Avoid guessing; request constraints/data or offer safer alternatives."
        )
    elif regex_list_match(needs_info, prompt):
        status = "NEEDS_INFO"
        reason = (
            "Prompt appears under-specified. Ask for the minimal missing inputs "
            "(repro steps, logs, code snippet, success criteria)."
        )

    if status and reason:
        activate_state(project_dir, status=status, reason=reason, kind="prompt")

        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "AFL ACTIVE (prompt preflight). "
                    "You must use the FAILURE MODE template instead of guessing. "
                    f"Status: {status}. Reason: {reason}"
                ),
            }
        }
        print(json.dumps(out))


if __name__ == "__main__":
    main()
