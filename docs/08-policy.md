# Policy reference (`afl_policy.json`)

This file configures triggers and feature flags.

## Top-level fields

- `version` — policy version (integer)
- `maxStopBlocks` — how many times Stop can block before failing open
- `features` — enable/disable each hook behavior:
  - `userPromptSubmit`
  - `stopGate`
  - `postToolUseFailure`
  - `postToolUse`
  - `preToolUse` (optional)
  - `taskCompleted` (optional)

- `requiredFailureModeHeadings` — regex patterns enforced by Stop gate
- `promptFailTriggers` — regex patterns to activate Failure Mode on user prompt:
  - `cannotVerify`: intrinsically unverifiable prompts
  - `needsInfo`: under-specified prompts

Optional (used only if `features.preToolUse=true`):
- `denyPathRegex`
- `denyBashRegex`
- `askBashRegex`

Optional (used only if `features.taskCompleted=true`):
- `taskCompleted.testCommand`
- `taskCompleted.autoDetect`

## Recommended workflow

1) Start with minimal features:
   - `userPromptSubmit=true`
   - `postToolUseFailure=true`
   - `stopGate=true`
   - everything else false

2) Tune `promptFailTriggers` to your domain:
   - add triggers for common "no correct answer" requests in your org
   - add triggers for chronic under-specification patterns in your org

3) Only then consider enabling:
   - `taskCompleted` for CI-like quality gates
   - `preToolUse` if you lack other safeguards
