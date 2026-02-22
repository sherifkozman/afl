import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_SRC = ROOT / "hooks"


class AflV3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)

        # Simulated HOME
        self.home = base / "home"
        (self.home / ".claude" / "hooks").mkdir(parents=True)
        (self.home / ".claude" / "rules").mkdir(parents=True)

        # Simulated project (no .claude directory by default)
        self.project = base / "project"
        self.project.mkdir(parents=True)

        # Copy hooks into HOME so imports work
        for f in HOOKS_SRC.glob("*.py"):
            dst = self.home / ".claude" / "hooks" / f.name
            dst.write_text(f.read_text())

        # Copy policy into HOME
        (self.home / ".claude" / "afl_policy.json").write_text((ROOT / "afl_policy.json").read_text())

        # Env
        self.env = dict(os.environ)
        self.env["HOME"] = str(self.home)
        self.env["CLAUDE_PROJECT_DIR"] = str(self.project)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, script: Path, payload: dict):
        p = subprocess.run(
            ["python3", str(script)],
            input=json.dumps(payload).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
        )
        out = p.stdout.decode().strip()
        err = p.stderr.decode().strip()
        return p.returncode, out, err

    def test_user_prompt_sets_state_in_global_dir_when_project_has_no_claude(self):
        script = self.home / ".claude" / "hooks" / "afl_user_prompt.py"

        rc, out, err = self.run_hook(
            script,
            {
                "cwd": str(self.project),
                "hook_event_name": "UserPromptSubmit",
                "prompt": "Predict the exact stock price of AAPL next Tuesday.",
            },
        )
        self.assertEqual(rc, 0)
        _ = json.loads(out)

        # State should be under ~/.claude/afl_state/<project-key>/afl_state.json
        state_root = self.home / ".claude" / "afl_state"
        self.assertTrue(state_root.exists())
        state_files = list(state_root.glob("*/afl_state.json"))
        self.assertEqual(len(state_files), 1)
        state = json.loads(state_files[0].read_text())
        self.assertTrue(state.get("active"))
        self.assertEqual(state.get("status"), "CANNOT_VERIFY")

        # Stop gate should block if assistant message doesn't use template
        stop = self.home / ".claude" / "hooks" / "afl_stop_gate.py"
        rc2, out2, err2 = self.run_hook(
            stop,
            {
                "cwd": str(self.project),
                "hook_event_name": "Stop",
                "last_assistant_message": "It will close at $245.32.",
            },
        )
        self.assertEqual(rc2, 0)
        j2 = json.loads(out2)
        self.assertEqual(j2["decision"], "block")

    def test_pretool_disabled_by_default(self):
        pre = self.home / ".claude" / "hooks" / "afl_pre_tool.py"
        rc, out, err = self.run_hook(
            pre,
            {
                "cwd": str(self.project),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
                "tool_use_id": "toolu_test",
            },
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_pretool_denies_when_enabled(self):
        # Enable preToolUse in the HOME policy
        policy_path = self.home / ".claude" / "afl_policy.json"
        policy = json.loads(policy_path.read_text())
        policy.setdefault("features", {})["preToolUse"] = True
        policy_path.write_text(json.dumps(policy))

        pre = self.home / ".claude" / "hooks" / "afl_pre_tool.py"
        rc, out, err = self.run_hook(
            pre,
            {
                "cwd": str(self.project),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
                "tool_use_id": "toolu_test",
            },
        )
        self.assertEqual(rc, 0)
        j = json.loads(out)
        self.assertEqual(j["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_stop_gate_clears_state_when_message_compliant(self):
        # Trigger failure mode via prompt
        up = self.home / ".claude" / "hooks" / "afl_user_prompt.py"
        rc, out, err = self.run_hook(
            up,
            {
                "cwd": str(self.project),
                "hook_event_name": "UserPromptSubmit",
                "prompt": "Fix the bug in my project.",
            },
        )
        self.assertEqual(rc, 0)

        stop = self.home / ".claude" / "hooks" / "afl_stop_gate.py"
        compliant = """FAILURE MODE

Status: NEEDS_INFO

Blocked because:
- Missing repro steps and logs.

To proceed I need:
- The exact command that fails and the stack trace.

Safe next actions (I can do now):
1) Tell you how to capture the stack trace.
"""
        rc2, out2, err2 = self.run_hook(
            stop,
            {
                "cwd": str(self.project),
                "hook_event_name": "Stop",
                "last_assistant_message": compliant,
            },
        )
        self.assertEqual(rc2, 0)
        self.assertEqual(out2, "")

        # State should be cleared
        state_root = self.home / ".claude" / "afl_state"
        state_files = list(state_root.glob("*/afl_state.json"))
        self.assertEqual(len(state_files), 1)
        state = json.loads(state_files[0].read_text())
        self.assertFalse(state.get("active"))

    def test_post_tool_failure_activates_state(self):
        pf = self.home / ".claude" / "hooks" / "afl_post_tool_failure.py"
        rc, out, err = self.run_hook(
            pf,
            {
                "cwd": str(self.project),
                "hook_event_name": "PostToolUseFailure",
                "tool_name": "Bash",
                "tool_use_id": "toolu_test",
                "error": "command not found: pytest",
            },
        )
        self.assertEqual(rc, 0)
        _ = json.loads(out)

        state_root = self.home / ".claude" / "afl_state"
        state_files = list(state_root.glob("*/afl_state.json"))
        self.assertEqual(len(state_files), 1)
        state = json.loads(state_files[0].read_text())
        self.assertTrue(state.get("active"))
        self.assertEqual(state.get("kind"), "tool_failure")


if __name__ == "__main__":
    unittest.main()
