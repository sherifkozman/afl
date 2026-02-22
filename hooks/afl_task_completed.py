#!/usr/bin/env python3
"""TaskCompleted hook.

Optional quality gate: run tests before allowing task completion.

Notes:
- TaskCompleted supports exit code control (exit 2 blocks completion). Docs.
- This can be expensive/noisy; default is OFF in policy.features.taskCompleted.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from afl_lib import activate_state, feature_enabled, load_hook_input, load_policy


def detect_test_command(project_dir: Path) -> Optional[str]:
    # JS / TS
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm test"
    if (project_dir / "yarn.lock").exists():
        return "yarn test"
    if (project_dir / "package.json").exists():
        return "npm test"

    # Python
    if (
        (project_dir / "pytest.ini").exists()
        or (project_dir / "pyproject.toml").exists()
        or (project_dir / "requirements.txt").exists()
    ):
        return "pytest"

    # Go
    if (project_dir / "go.mod").exists():
        return "go test ./..."

    # Rust
    if (project_dir / "Cargo.toml").exists():
        return "cargo test"

    return None


def main() -> int:
    data, project_dir = load_hook_input()
    policy = load_policy(project_dir)

    if not feature_enabled(policy, "taskCompleted"):
        return 0

    tc_cfg = (policy.get("taskCompleted") or {})
    test_cmd = (tc_cfg.get("testCommand") or "").strip()

    if not test_cmd and tc_cfg.get("autoDetect", True):
        test_cmd = detect_test_command(project_dir) or ""

    if not test_cmd:
        return 0

    proc = subprocess.run(
        test_cmd,
        shell=True,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if proc.returncode == 0:
        return 0

    output = (proc.stdout or "").strip()
    tail = "\n".join(output.splitlines()[-25:]) if output else "(no output)"
    reason = f"Test command failed: `{test_cmd}`\n{tail}"

    activate_state(
        project_dir,
        status="CANNOT_VERIFY",
        kind="tests_failed",
        reason=reason,
        tool_name="TaskCompleted",
        tool_use_id=None,
    )

    sys.stderr.write("AFL: Task cannot be marked complete because tests failed.\n")
    sys.stderr.write(f"Command: {test_cmd}\n")
    sys.stderr.write("Output (tail):\n")
    sys.stderr.write(tail + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
