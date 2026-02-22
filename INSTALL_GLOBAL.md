# Install AFL (Agent Failure Mode) globally

This repo is designed to work as a **user-level install** in `~/.claude/` and to **coexist with other global hooks**.

## What this pack does

- Policy lookup supports `~/.claude/afl_policy.json` fallback
- State is stored under `~/.claude/afl_state/<project-key>/...` when the repo has no `.claude/` directory (avoids polluting repos)
- Feature flags let you enable only the core "cannot verify / needs info" behavior

## Quick install (minimal)

From the repo root:

```bash
python3 install_global.py
```

## Full install (still feature-gated)

```bash
python3 install_global.py --full
```

## Restart + verify

The host agent snapshots hook config at startup. Restart after installation.

Then in the host agent:
- run `/hooks` to confirm the new `[User]` hooks are present
- enable verbose mode (`Ctrl+O`) to see hook execution logs

## Policy knobs

Edit:

- `~/.claude/afl_policy.json`

Recommended starting point:
- keep `features.preToolUse = false` if you already have command blockers
- keep `features.taskCompleted = false` unless you want a test gate

## Removal

- Remove hook entries from `~/.claude/settings.json` (or via `/hooks` menu)
- Delete `~/.claude/hooks/afl_*.py`
- Delete `~/.claude/afl_policy.json` (optional)
- Delete `~/.claude/rules/10-failure-mode.md` (optional)
