"""Private response parsing helpers for the Google-compatible provider."""

from __future__ import annotations

from typing import Any

from core.schemas import DiagnosticCode, GeneratedImageValue, ProviderDiagnosticFact


def extract_images(
    response: Any,
    *,
    model_name: str,
    requested_resolution: str | None,
    facts: list[ProviderDiagnosticFact],
    append_fact,
    materialize_generated_image,
    sanitize_source_uri,
) -> list[GeneratedImageValue]:
    """Extract and materialize images from a Google-compatible SDK response."""
    images: list[GeneratedImageValue] = []
    if response and response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = bytes(part.inline_data.data)
                images.append(
                    materialize_generated_image(
                        image_bytes=image_bytes,
                        mime_type=getattr(part.inline_data, "mime_type", None),
                        model_name=model_name,
                        requested_resolution=requested_resolution,
                        facts=facts,
                        source_uri=_extract_part_source_uri(part),
                        source_kind="inline_data",
                    )
                )
                continue

            file_data = getattr(part, "file_data", None)
            if file_data and getattr(file_data, "file_uri", None):
                append_fact(
                    facts,
                    DiagnosticCode.GENERATED_IMAGE_REMOTE_ONLY_UNSUPPORTED,
                    {
                        "mime_type": getattr(file_data, "mime_type", None),
                        "source_uri": sanitize_source_uri(file_data.file_uri),
                        "source_kind": "file_uri",
                    },
                )
    return images


def _extract_part_source_uri(part: Any) -> str | None:
    """Extract the most useful source URI from a Google Part when available."""
    file_data = getattr(part, "file_data", None)
    if file_data and getattr(file_data, "file_uri", None):
        return str(file_data.file_uri)
    return None
