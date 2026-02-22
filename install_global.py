#!/usr/bin/env python3
"""Install AFL (Agent Failure Mode) (v3) into ~/.claude without clobbering existing setup.

- Copies hook scripts into ~/.claude/hooks/
- Copies afl_policy.json into ~/.claude/afl_policy.json (does not overwrite by default)
- Copies rules/10-failure-mode.md into ~/.claude/rules/
- Ensures ~/.claude/CLAUDE.md imports the rule file
- Merges minimal hook entries into ~/.claude/settings.json

Usage:
  python3 install_global.py           # minimal install
  python3 install_global.py --full    # installs all hook entries (still feature-gated by policy)
  python3 install_global.py --force-policy  # overwrite policy (backs up first)

Note: the agent runtime snapshots hooks at startup; restart and then review via /hooks.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def backup(path: Path) -> None:
    if not path.exists():
        return
    bak = path.with_name(path.name + f".bak.{_ts()}")
    shutil.copy2(path, bak)


def ensure_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n")


def dedupe_hook_handlers(handlers: list) -> list:
    seen = set()
    out = []
    for h in handlers:
        # key on type + command/prompt
        t = h.get("type")
        if t == "command":
            key = (t, h.get("command"))
        elif t == "prompt":
            key = (t, h.get("prompt"))
        else:
            key = (t, json.dumps(h, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def merge_hooks(existing: dict, addition: dict) -> dict:
    ex = dict(existing)
    ex.setdefault("hooks", {})

    add_hooks = (addition.get("hooks") or {})
    for event, matchers in add_hooks.items():
        ex["hooks"].setdefault(event, [])
        # naive concat; then dedupe identical handlers inside each matcher
        ex["hooks"][event].extend(matchers)

        # Deduplicate identical handlers per matcher entry
        cleaned = []
        for m in ex["hooks"][event]:
            m2 = dict(m)
            if "hooks" in m2 and isinstance(m2["hooks"], list):
                m2["hooks"] = dedupe_hook_handlers(m2["hooks"])
            cleaned.append(m2)
        ex["hooks"][event] = cleaned

    return ex


def ensure_import_line(claude_md: Path, import_line: str) -> None:
    if not claude_md.exists():
        claude_md.write_text(import_line + "\n")
        return

    txt = claude_md.read_text()
    if import_line in txt:
        return

    backup(claude_md)
    claude_md.write_text(txt.rstrip() + "\n\n" + import_line + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="Install full hook set (feature-gated)")
    ap.add_argument("--force-policy", action="store_true", help="Overwrite ~/.claude/afl_policy.json")
    args = ap.parse_args()

    home = Path.home() / ".claude"
    ensure_dir(home)

    # Copy hooks
    hooks_src = HERE / "hooks"
    hooks_dst = home / "hooks"
    ensure_dir(hooks_dst)

    for f in hooks_src.glob("*.py"):
        dst = hooks_dst / f.name
        shutil.copy2(f, dst)
        dst.chmod(0o755)

    # Copy policy
    policy_src = HERE / "afl_policy.json"
    policy_dst = home / "afl_policy.json"

    if policy_dst.exists() and not args.force_policy:
        # keep existing
        pass
    else:
        if policy_dst.exists():
            backup(policy_dst)
        shutil.copy2(policy_src, policy_dst)

    # Copy rules
    rules_src = HERE / "rules" / "10-failure-mode.md"
    rules_dst_dir = home / "rules"
    ensure_dir(rules_dst_dir)
    rules_dst = rules_dst_dir / "10-failure-mode.md"

    if rules_dst.exists():
        backup(rules_dst)
    shutil.copy2(rules_src, rules_dst)

    # Ensure CLAUDE.md import
    claude_md = home / "CLAUDE.md"
    ensure_import_line(claude_md, "@~/.claude/rules/10-failure-mode.md")

    # Merge settings
    settings_path = home / "settings.json"
    if settings_path.exists():
        backup(settings_path)

    existing = load_json(settings_path) if settings_path.exists() else {}
    addition_path = HERE / "settings" / ("settings.afl.full.json" if args.full else "settings.afl.minimal.json")
    addition = load_json(addition_path)

    merged = merge_hooks(existing, addition)
    save_json(settings_path, merged)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
