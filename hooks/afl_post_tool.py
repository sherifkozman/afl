#!/usr/bin/env python3
"""PostToolUse hook.

Clears state after successful tool execution.
Rationale: if a tool call succeeded, we don't want stale "needs permission" or
"blocked" flags forcing future Failure Mode.
"""

from __future__ import annotations

from afl_lib import clear_state, feature_enabled, load_hook_input, load_policy


def main() -> None:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "postToolUse"):
        return

    # Conservative: clear whenever any tool succeeded.
    clear_state(project_dir)


if __name__ == "__main__":
    main()
