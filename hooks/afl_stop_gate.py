#!/usr/bin/env python3
"""Stop hook.

Enforces structured FAILURE MODE output when state.active is set.

Why Stop? Because it's the only guaranteed chance to inspect the final assistant
message and block completion until the response matches the required template.

Safety: maxStopBlocks prevents infinite loops; after N blocks, it fails open.
"""

from __future__ import annotations

import json

from afl_lib import (
    clear_state,
    feature_enabled,
    is_failure_mode_message_compliant,
    load_hook_input,
    load_policy,
    load_state,
    save_state,
)


def main() -> None:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "stopGate"):
        return

    state = load_state(project_dir)
    if not state.get("active"):
        return

    message = data.get("last_assistant_message") or ""
    if is_failure_mode_message_compliant(message, policy):
        # Good: clear state so we don't keep blocking.
        clear_state(project_dir)
        return

    # Not compliant: block stop until template is used.
    attempts = int(state.get("attempts") or 0) + 1
    state["attempts"] = attempts
    save_state(project_dir, state)

    max_blocks = int(policy.get("maxStopBlocks") or 2)
    if attempts > max_blocks:
        # Fail open to avoid deadlocks.
        clear_state(project_dir)
        return

    reason = state.get("reason") or "A prior condition triggered FAILURE MODE."
    status = state.get("status") or "CANNOT_VERIFY"

    out = {
        "decision": "block",
        "reason": (
            "AFL: You must respond using the FAILURE MODE template. "
            f"Status should be {status}. Trigger: {reason}"
        ),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
