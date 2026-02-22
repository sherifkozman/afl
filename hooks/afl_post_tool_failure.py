#!/usr/bin/env python3
"""PostToolUseFailure hook.

If a tool fails, we activate FAILURE MODE state so Claude must acknowledge
uncertainty and propose safe recovery steps instead of fabricating results.
"""

from __future__ import annotations

import json

from afl_lib import activate_state, feature_enabled, load_hook_input, load_policy


def main() -> None:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "postToolUseFailure"):
        return

    tool_name = data.get("tool_name")
    tool_use_id = data.get("tool_use_id")
    err = (data.get("error") or "Tool execution failed.").strip()

    activate_state(
        project_dir,
        status="CANNOT_VERIFY",
        reason=f"Tool {tool_name} failed: {err}",
        kind="tool_failure",
        tool_name=tool_name,
        tool_use_id=tool_use_id,
    )

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": (
                "AFL ACTIVE (tool failure). "
                "Do NOT claim success. Use FAILURE MODE template with recovery steps. "
                f"Failure: {tool_name}: {err}"
            ),
        }
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
