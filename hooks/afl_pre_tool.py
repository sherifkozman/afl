#!/usr/bin/env python3
"""PreToolUse hook.

Optional safety layer (often overlaps with existing agent runtime permission harness).
Default: disabled via policy.features.preToolUse = false.

If enabled, it:
- Denies access to sensitive paths (denyPathRegex)
- Denies dangerous Bash commands (denyBashRegex)
- Asks for confirmation on risky-but-plausible Bash (askBashRegex)

Note: Hook semantics for multiple PreToolUse hooks can be ambiguous; keep this
layer minimal if you already have strong global blockers.
"""

from __future__ import annotations

import json

from afl_lib import (
    feature_enabled,
    load_hook_input,
    load_policy,
    regex_list_match,
)


def _out(decision: str, reason: str, *, updated_input=None):
    obj = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    if updated_input is not None:
        obj["hookSpecificOutput"]["updatedInput"] = updated_input
    return obj


def main() -> None:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "preToolUse"):
        return

    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input") or {}

    # File tools: Read/Edit/Write
    if tool_name in ("Read", "Edit", "Write"):
        path = (tool_input.get("file_path") or "").strip()
        if path and regex_list_match(policy.get("denyPathRegex"), path):
            print(json.dumps(_out("deny", f"Blocked sensitive path by policy: {path}")))
        return

    # Bash tool
    if tool_name == "Bash":
        cmd = (tool_input.get("command") or "").strip()
        if not cmd:
            return

        if regex_list_match(policy.get("denyBashRegex"), cmd):
            print(json.dumps(_out("deny", "Blocked dangerous shell command by policy.")))
            return

        if regex_list_match(policy.get("askBashRegex"), cmd):
            print(json.dumps(_out("ask", "Command is risky; user confirmation required.")))
            return


if __name__ == "__main__":
    main()
