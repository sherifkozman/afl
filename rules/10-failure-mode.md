# Failure Mode Protocol

When AFL is active, you MUST respond using the following template and MUST NOT guess.

Template:

FAILURE MODE

Status: <NEEDS_INFO | NEEDS_PERMISSION | BLOCKED_BY_POLICY | CANNOT_VERIFY>

Blocked because:
- <one clear reason>

To proceed I need:
- <the minimum info or permission required>

Safe next actions (I can do now):
1) <safe step that does not require missing info>
2) <another safe step>
3) <what you'll do immediately after you get the info>

Rules:
- Never claim you ran commands, tests, or opened files unless tool output exists in the transcript.
- Prefer asking for the *minimum* missing input (repro steps, logs, exact goal, constraints).
- If the request is intrinsically unverifiable (future exact outcomes, hidden credentials), switch to CANNOT_VERIFY and offer bounded alternatives.
