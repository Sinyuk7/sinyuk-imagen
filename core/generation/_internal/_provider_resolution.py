"""Resolution token and warning helpers for provider implementations."""

from __future__ import annotations

from typing import Any, Callable

from core.schemas import DiagnosticCode, GeneratedImageArtifact, ProviderDiagnosticFact


def normalize_resolution_token(value: Any) -> str | None:
    """Normalize a symbolic resolution token into a stable uppercase form."""
    if value is None:
        return None
    text = str(value).strip().upper()
    return text or None


def minimum_long_edge_for_resolution(value: str | None) -> int | None:
    """Map supported symbolic resolution tokens to the minimum expected long edge."""
    resolution_to_edge = {
        "0.5K": 512,
        "1K": 1024,
        "2K": 2048,
        "4K": 4096,
    }
    return resolution_to_edge.get(value or "")


def append_generated_image_resolution_fact(
    *,
    facts: list[ProviderDiagnosticFact],
    artifact: GeneratedImageArtifact,
    requested_resolution: str | None,
    append_fact: Callable[
        [list[ProviderDiagnosticFact], DiagnosticCode, dict[str, object] | None],
        None,
    ],
) -> None:
    """Emit a warning when a generated image is smaller than the requested size."""
    normalized_resolution = normalize_resolution_token(requested_resolution)
    minimum_long_edge = minimum_long_edge_for_resolution(normalized_resolution)
    if minimum_long_edge is None:
        return

    actual_long_edge = max(artifact.width, artifact.height)
    if actual_long_edge >= minimum_long_edge:
        return

    append_fact(
        facts,
        DiagnosticCode.GENERATED_IMAGE_RESOLUTION_MISMATCH,
        {
            "requested_resolution": normalized_resolution,
            "minimum_expected_long_edge": minimum_long_edge,
            "actual_width": artifact.width,
            "actual_height": artifact.height,
            "actual_long_edge": actual_long_edge,
            "download_name": artifact.download_name,
        },
    )
