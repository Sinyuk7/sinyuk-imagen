"""Diagnostic helpers shared by provider implementations."""

from __future__ import annotations

from typing import Any

from core.generation._internal._provider_resolution import normalize_resolution_token
from core.schemas import DiagnosticCode, ProviderDiagnosticFact, TaskConfig


def append_fact(
    facts: list[ProviderDiagnosticFact],
    code: DiagnosticCode,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append a structured provider diagnostic fact."""
    facts.append(ProviderDiagnosticFact(code=code, payload=payload or {}))


def validate_requested_resolution(
    task_config: TaskConfig,
    model_name: str,
    supported_resolutions: list[str] | None,
    facts: list[ProviderDiagnosticFact],
) -> str | None:
    """Validate a requested resolution token against model support."""
    requested_resolution = normalize_resolution_token(task_config.params.get("resolution"))
    if requested_resolution is None or not supported_resolutions:
        return None

    normalized_supported = [
        normalize_resolution_token(value) or str(value)
        for value in supported_resolutions
    ]
    if requested_resolution in normalized_supported:
        return None

    append_fact(
        facts,
        DiagnosticCode.REQUESTED_RESOLUTION_UNSUPPORTED,
        {
            "model_name": model_name,
            "requested_resolution": requested_resolution,
            "supported_resolutions": normalized_supported,
        },
    )
    supported_text = ", ".join(normalized_supported)
    return (
        f"Model '{model_name}' does not support resolution '{requested_resolution}'. "
        f"Supported resolutions: {supported_text}."
    )
