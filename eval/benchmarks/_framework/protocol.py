"""AFL protocol management and model response generation."""

from __future__ import annotations

import re
import time
from pathlib import Path

from .types import ModelResponse

_AFL_STATUS_RE = re.compile(
    r"^Status:\s*(NEEDS_INFO|NEEDS_PERMISSION|BLOCKED_BY_POLICY|CANNOT_VERIFY)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_FAILURE_MODE_RE = re.compile(r"^FAILURE MODE\b", re.IGNORECASE | re.MULTILINE)


def load_afl_protocol(project_root: Path | None = None) -> str:
    """Read and return the AFL failure-mode protocol text.

    Args:
        project_root: Path to the project root. If None, auto-detected from
                      this file's location (../../.. relative to _framework/).

    Returns:
        Content of rules/10-failure-mode.md.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    protocol_path = project_root / "rules" / "10-failure-mode.md"
    return protocol_path.read_text(encoding="utf-8")


def build_system_prompt(base_prompt: str = "", with_afl: bool = True) -> str:
    """Build a system prompt, optionally prepending the AFL protocol.

    Args:
        base_prompt: The base system prompt to use.
        with_afl: If True, prepend the AFL protocol text.

    Returns:
        The final system prompt string.
    """
    if not with_afl:
        return base_prompt

    protocol = load_afl_protocol()
    if base_prompt:
        return f"{protocol}\n\n{base_prompt}"
    return protocol


def parse_afl_response(text: str) -> tuple[bool, str | None]:
    """Quick check: does the response contain the AFL failure mode template?

    Args:
        text: Model response text.

    Returns:
        (is_abstention, status) where status is the extracted Status value or None.
    """
    if not text:
        return False, None
    if not _FAILURE_MODE_RE.search(text):
        return False, None
    status_match = _AFL_STATUS_RE.search(text)
    status = status_match.group(1).upper() if status_match else None
    return True, status


def generate_response(
    prompt: str,
    system: str,
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    base_url: str | None = None,
    vertex: bool = False,
    project: str | None = None,
    location: str = "us-central1",
    temperature: float = 0.0,
) -> ModelResponse:
    """Call the OpenAI-compatible API and return a ModelResponse.

    Args:
        prompt: The user-facing prompt.
        system: The system prompt (use build_system_prompt to construct).
        model: Model identifier.
        api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
        base_url: Custom base URL for OpenAI-compatible endpoints.
        vertex: If True, authenticate via Google ADC for Vertex AI.
        project: GCP project ID (for Vertex AI mode).
        location: GCP region (for Vertex AI mode).
        temperature: Sampling temperature (default 0.0 for reproducibility).

    Returns:
        ModelResponse with is_abstention and afl_status populated, plus
        latency_ms in metadata.
    """
    from .client import create_client  # noqa: PLC0415

    client = create_client(
        api_key=api_key,
        base_url=base_url,
        vertex=vertex,
        project=project,
        location=location,
    )

    t0 = time.monotonic()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    latency_ms = (time.monotonic() - t0) * 1000.0

    text = completion.choices[0].message.content or ""
    is_abstention, afl_status = parse_afl_response(text)

    return ModelResponse(
        text=text,
        is_abstention=is_abstention,
        afl_status=afl_status,
        metadata={
            "latency_ms": round(latency_ms, 1),
            "model": model,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens
                if completion.usage
                else None,
                "completion_tokens": completion.usage.completion_tokens
                if completion.usage
                else None,
            },
        },
    )
