"""Generic LLM-as-judge utility for AFL benchmark scoring."""

from __future__ import annotations

import json


def call_judge(
    system: str,
    user_content: str,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    vertex: bool = False,
    project: str | None = None,
    location: str = "us-central1",
) -> dict:
    """Call an LLM judge with a system prompt and parse JSON response.

    Args:
        system: Judge system prompt defining scoring criteria.
        user_content: The content to evaluate.
        model: Judge model identifier.
        api_key: API key (falls back to OPENAI_API_KEY env var).
        base_url: Custom OpenAI-compatible base URL.
        vertex: If True, use Vertex AI with ADC auth.
        project: GCP project ID (for Vertex AI).
        location: GCP region (for Vertex AI).

    Returns:
        Parsed JSON dict from the judge response.
    """
    from .client import create_client  # noqa: PLC0415

    client = create_client(
        api_key=api_key,
        base_url=base_url,
        vertex=vertex,
        project=project,
        location=location,
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    raw = completion.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": raw}
