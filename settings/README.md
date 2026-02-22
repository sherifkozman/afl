# settings/

These are snippet files intended to be merged into the agent runtime's `~/.claude/settings.json`:

- `settings.afl.minimal.json` — core hooks only (recommended)
- `settings.afl.full.json` — includes optional PreToolUse + TaskCompleted hooks

The installer (`install_global.py`) reads these files depending on `--full`.
