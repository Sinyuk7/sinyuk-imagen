"""Private async client helpers for the Google-compatible provider."""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types


def build_async_client(
    *,
    api_key: str,
    api_version: str,
    base_url: str,
) -> Any:
    """Create one SDK client for a single async request."""
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            api_version=api_version,
            base_url=base_url,
        ),
    )


async def generate_content(
    client: Any,
    *,
    model: str,
    contents: list[Any],
    config: Any,
) -> Any:
    """Send one async generate-content request and close client resources."""
    try:
        return await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    finally:
        aio_client = getattr(client, "aio", None)
        if aio_client is not None and hasattr(aio_client, "aclose"):
            await aio_client.aclose()
        if hasattr(client, "close"):
            client.close()
