# Installation

## Global install (recommended)

### Minimal install (core "cannot verify / cannot complete" use case)
From the repo root:

```bash
python3 install_global.py
```

This will:
- copy hook scripts to `~/.claude/hooks/`
- copy `afl_policy.json` to `~/.claude/afl_policy.json` (no overwrite by default)
- copy `rules/10-failure-mode.md` to `~/.claude/rules/`
- ensure `~/.claude/CLAUDE.md` imports the rule file
- merge minimal hooks into `~/.claude/settings.json` (backups created automatically)

Restart the host agent afterwards.

### Full install (optional)
```bash
python3 install_global.py --full
```

This adds `PreToolUse` and `TaskCompleted` entries as well.
They remain feature-gated in `afl_policy.json`.

## Verifying installation

In the host agent:
- run `/hooks` to see the active hooks and their scope (`[User]` vs `[Project]`)
- enable verbose mode (`Ctrl+O`) to view hook logs

## Project-level install (per repo)

Use this when:
- you want repo-specific policies, or
- you want to enable AFL for one project only.

Suggested pattern:

1) Create `.claude/` inside the target repo:
   - `.claude/settings.json`
   - `.claude/afl_policy.json`
   - `.claude/rules/10-failure-mode.md`

2) Reference hook scripts from a stable path:
   - simplest: keep hook scripts in `~/.claude/hooks/` and reference that path
   - advanced: vendor hook scripts inside the repo and reference `"$CLAUDE_PROJECT_DIR"/.claude/hooks/...`

3) Restart the host agent and verify with `/hooks`.

## Avoiding conflicts with existing global hooks

If you already have:
- a global `PreToolUse` command blocker,
- a sensitive-file protector,
- or a completion verifier,

start with minimal install and keep `features.preToolUse = false` in `afl_policy.json`.

AFL's core value is *not* command blocking — it's preventing "no-correct-answer" hallucinations.
