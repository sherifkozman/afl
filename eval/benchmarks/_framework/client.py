"""OpenAI client factory with Vertex AI (ADC) and custom endpoint support."""

from __future__ import annotations

import os


def create_client(
    api_key: str | None = None,
    base_url: str | None = None,
    vertex: bool = False,
    project: str | None = None,
    location: str = "us-central1",
):
    """Create an OpenAI-compatible client.

    Modes:
      - vertex=True: Uses Google ADC to get a bearer token and builds the
        Vertex AI OpenAPI endpoint URL.
      - base_url provided: Any OpenAI-compatible endpoint.
      - Neither: Standard OpenAI client.

    Args:
        api_key: API key for OpenAI or compatible endpoint.
        base_url: Custom base URL for OpenAI-compatible endpoints.
        vertex: If True, authenticate via Google ADC for Vertex AI.
        project: GCP project ID (required for vertex; falls back to
                 GOOGLE_CLOUD_PROJECT env var).
        location: GCP region (default us-central1; falls back to
                  GOOGLE_CLOUD_LOCATION env var).

    Returns:
        An openai.OpenAI client instance.
    """
    try:
        import openai  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "openai package is required. Install with: pip install openai"
        ) from exc

    if vertex:
        return _create_vertex_client(openai, project, location)

    resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
    return openai.OpenAI(api_key=resolved_key, base_url=base_url)


def _create_vertex_client(openai_module, project: str | None, location: str):
    """Build an OpenAI client pointing at Vertex AI with ADC auth."""
    try:
        import google.auth  # noqa: PLC0415
        import google.auth.transport.requests  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "google-auth package is required for Vertex AI mode. "
            "Install with: pip install google-auth"
        ) from exc

    resolved_project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not resolved_project:
        raise ValueError(
            "GCP project is required for Vertex AI. "
            "Pass --project or set GOOGLE_CLOUD_PROJECT."
        )

    resolved_location = location or os.environ.get(
        "GOOGLE_CLOUD_LOCATION", "us-central1"
    )

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())

    if resolved_location == "global":
        host = "aiplatform.googleapis.com"
    else:
        host = f"{resolved_location}-aiplatform.googleapis.com"

    base_url = (
        f"https://{host}/v1/"
        f"projects/{resolved_project}/locations/{resolved_location}/"
        f"endpoints/openapi"
    )

    return openai_module.OpenAI(
        api_key=credentials.token,
        base_url=base_url,
    )
