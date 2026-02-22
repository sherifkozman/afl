#!/usr/bin/env python3
"""Shared utilities for AFL (Agent Failure Mode) hook scripts.

v3 goals (practical global install):
- Works when installed *project-level* (./.claude/...) OR *user-level* (~/.claude/...)
- Does NOT create new .claude/ folders inside repos unless a repo already has one
- Policy lookup order:
    1) <project>/.claude/afl_policy.json (if present)
    2) ~/.claude/afl_policy.json
- State storage:
    - If <project>/.claude exists: <project>/.claude/state/afl_state.json
    - Else: ~/.claude/afl_state/<project-key>/afl_state.json

No external deps (stdlib only). JSON in / JSON out.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

STATE_FILENAME = "afl_state.json"
POLICY_FILENAME = "afl_policy.json"


def _read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def _home_claude_dir() -> Path:
    return (Path.home() / ".claude").expanduser().resolve()


def _find_git_root(start: Path) -> Optional[Path]:
    """Walk parents until we find a .git directory."""
    try:
        p = start.resolve()
    except Exception:
        p = start

    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def _find_project_dir_from_cwd(cwd: str) -> Path:
    """Best-effort project root discovery.

    Priority:
    1) CLAUDE_PROJECT_DIR env var (recommended by the agent runtime docs)
    2) git root (directory containing .git)
    3) cwd
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    p = Path(cwd or os.getcwd()).expanduser().resolve()
    git_root = _find_git_root(p)
    if git_root is not None:
        return git_root

    return p


def load_hook_input() -> Tuple[Dict[str, Any], Path]:
    data = _read_stdin_json()
    cwd = data.get("cwd") or os.getcwd()
    project_dir = _find_project_dir_from_cwd(cwd)
    return data, project_dir


def _project_has_local_claude_dir(project_dir: Path) -> bool:
    return (project_dir / ".claude").is_dir()


def _project_key(project_dir: Path) -> str:
    """Stable key for global state storage.

    Uses basename + short hash of full path to avoid collisions.
    """
    path_str = str(project_dir.resolve())
    h = hashlib.sha1(path_str.encode("utf-8")).hexdigest()[:10]
    name = project_dir.name or "project"
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return f"{safe}-{h}"


def policy_file(project_dir: Path) -> Path:
    local = project_dir / ".claude" / POLICY_FILENAME
    if local.exists():
        return local
    return _home_claude_dir() / POLICY_FILENAME


def state_file(project_dir: Path) -> Path:
    """Where to store runtime state."""
    if _project_has_local_claude_dir(project_dir):
        d = project_dir / ".claude" / "state"
        d.mkdir(parents=True, exist_ok=True)
        return d / STATE_FILENAME

    # Global fallback (do not create <project>/.claude)
    d = _home_claude_dir() / "afl_state" / _project_key(project_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / STATE_FILENAME


def load_policy(project_dir: Path) -> Dict[str, Any]:
    # Defaults are intentionally conservative.
    default: Dict[str, Any] = {
        "version": 3,
        "maxStopBlocks": 2,
        "features": {
            # Default choices for GLOBAL install friendliness:
            # - core use case (unanswerable/underspecified) is on
            # - dangerous commands/path protections are often already handled elsewhere
            "userPromptSubmit": True,
            "stopGate": True,
            "postToolUseFailure": True,
            "postToolUse": True,
            "preToolUse": False,
            "taskCompleted": False,
        },
        "requiredFailureModeHeadings": [
            r"^FAILURE MODE\b",
            r"^Status:\s*",
            r"^Blocked because:\s*",
            r"^To proceed I need:\s*",
            r"^Safe next actions\s*\(I can do now\):\s*",
        ],
        # Safety lists (only used if features.preToolUse = true)
        "denyPathRegex": [
            r"(^|/)\.env$",
            r"\.pem$",
            r"\.key$",
            r"id_rsa$",
        ],
        "denyBashRegex": [
            r"\brm\s+-rf\s+/\s*(?:$|[;&|])",
            r"\bmkfs\b",
            r"\bdd\s+if=",
            r"\bcurl\b.*\|\s*(sh|bash)\b",
            r"\bwget\b.*\|\s*(sh|bash)\b",
        ],
        "askBashRegex": [
            r"\bgit\s+push\b",
            r"\bgit\s+reset\s+--hard\b",
            r"\bterraform\s+apply\b",
            r"\bkubectl\s+apply\b",
        ],
        # Prompt triggers (core: unanswerable / under-specified)
        "promptFailTriggers": {
            "cannotVerify": [
                r"\bpredict\b.*\bexact\b",
                r"\bexact\s+stock\s+price\b",
                r"\bnext\s+(week|tuesday|month)\b.*\bprice\b",
                r"\bguarantee\b.*\b(outcome|result)\b",
            ],
            "needsInfo": [
                r"\bdebug\b.*\bno\s+context\b",
                r"\bfix\s+the\s+bug\b(?!.*(log|stack|repro|steps))",
                r"\brefactor\b(?!.*(goal|metric|constraint))",
            ],
        },
        "taskCompleted": {"testCommand": "", "autoDetect": True},
    }

    pf = policy_file(project_dir)
    if not pf.exists():
        return default

    try:
        loaded = json.loads(pf.read_text())
        # shallow-merge (1-level)
        merged = dict(default)
        for k, v in loaded.items():
            if v is None:
                continue
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return merged
    except Exception:
        # If policy is broken, fail open (do not break the agent).
        return default


def load_state(project_dir: Path) -> Dict[str, Any]:
    sf = state_file(project_dir)
    if not sf.exists():
        return {"active": False}
    try:
        return json.loads(sf.read_text())
    except Exception:
        return {"active": False}


def save_state(project_dir: Path, state: Dict[str, Any]) -> None:
    sf = state_file(project_dir)
    sf.write_text(json.dumps(state, indent=2))


def clear_state(project_dir: Path) -> None:
    save_state(project_dir, {"active": False})


def activate_state(
    project_dir: Path,
    *,
    status: str,
    reason: str,
    kind: str,
    tool_name: Optional[str] = None,
    tool_use_id: Optional[str] = None,
) -> None:
    state = {
        "active": True,
        "status": status,
        "kind": kind,
        "reason": reason,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "attempts": 0,
    }
    save_state(project_dir, state)


def is_failure_mode_message_compliant(message: str, policy: Dict[str, Any]) -> bool:
    if not message:
        return False
    required = policy.get("requiredFailureModeHeadings") or []
    lines = message.splitlines()
    for pattern in required:
        rx = re.compile(pattern, flags=re.IGNORECASE)
        if not any(rx.search(line.strip()) for line in lines):
            return False
    return True


def feature_enabled(policy: Dict[str, Any], key: str) -> bool:
    feats = policy.get("features") or {}
    return bool(feats.get(key, False))


def regex_list_match(patterns: Any, text: str) -> bool:
    if not patterns or not text:
        return False
    for pat in patterns:
        try:
            if re.search(pat, text, flags=re.IGNORECASE):
                return True
        except re.error:
            # Ignore bad regex
            continue
    return False
