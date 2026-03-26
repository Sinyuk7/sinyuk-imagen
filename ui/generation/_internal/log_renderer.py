"""Render provider diagnostics into compact UI markdown."""

from __future__ import annotations

import json

from core.schemas import (
    DiagnosticCode,
    GenerationResult,
    ProviderDiagnosticFact,
    ProviderDiagnostics,
)
from ui.generation._internal.status_formatter import shorten_error


def render_logcat(
    result: GenerationResult | None = None,
    diagnostics: ProviderDiagnostics | None = None,
    error_message: str | None = None,
) -> str:
    """Render provider diagnostics into concise markdown for the UI panel."""
    effective_diagnostics = diagnostics or (result.diagnostics if result else None)
    facts = list(effective_diagnostics.facts or []) if effective_diagnostics else []
    visible_facts = [fact for fact in facts if should_render_fact(fact)]
    blocks: list[str] = []
    if visible_facts:
        blocks.append("## Log")
    for fact in visible_facts:
        if fact.code == DiagnosticCode.REQUEST_SNAPSHOT:
            blocks.extend(
                [
                    "### Request Snapshot",
                    "```json",
                    json.dumps(fact.payload, ensure_ascii=False, indent=2),
                    "```",
                ]
            )
            continue

        message = format_fact_message(fact)
        if message:
            blocks.append(f"- {message}")
    if error_message and error_message.strip():
        if blocks:
            blocks.append("")
        blocks.extend(
            [
                "## Technical Error",
                "```text",
                error_message.strip(),
                "```",
            ]
        )
    return "\n".join(blocks)


def should_render_fact(fact: ProviderDiagnosticFact) -> bool:
    """Return whether the fact should be shown in the UI log panel."""
    return fact.code in {
        DiagnosticCode.GENERATED_IMAGE_MATERIALIZED,
        DiagnosticCode.GENERATED_IMAGE_REMOTE_ONLY_UNSUPPORTED,
        DiagnosticCode.GENERATED_IMAGE_RESOLUTION_MISMATCH,
        DiagnosticCode.GENERATED_IMAGE_SOURCE_RECORDED,
        DiagnosticCode.RESOLVED_MODEL,
        DiagnosticCode.REQUESTED_RESOLUTION_UNSUPPORTED,
        DiagnosticCode.REQUEST_NOT_SENT,
        DiagnosticCode.REFERENCE_IMAGE_LOADED,
        DiagnosticCode.RESPONSE_RECEIVED,
        DiagnosticCode.PROVIDER_ERROR,
        DiagnosticCode.REQUEST_SNAPSHOT,
    }


def format_fact_message(fact: ProviderDiagnosticFact) -> str:
    """Format a single structured diagnostic fact into UI text."""
    payload = fact.payload
    if fact.code == DiagnosticCode.RESOLVED_MODEL:
        return (
            f"Model: `{payload.get('model_display_name', 'unknown')}`"
            f" -> `{payload.get('model_name', 'unknown')}`"
        )
    if fact.code == DiagnosticCode.REQUEST_NOT_SENT:
        return "Dry run: request not sent."
    if fact.code == DiagnosticCode.REFERENCE_IMAGE_LOADED:
        return "Reference image: loaded."
    if fact.code == DiagnosticCode.GENERATED_IMAGE_MATERIALIZED:
        return (
            "Image: "
            f"`{payload.get('width', '?')}x{payload.get('height', '?')}` "
            f"({payload.get('mime_type', 'unknown')}, {payload.get('source_kind', 'unknown')})."
        )
    if fact.code == DiagnosticCode.GENERATED_IMAGE_SOURCE_RECORDED:
        return f"Source: `{payload.get('source_uri', 'unknown')}`."
    if fact.code == DiagnosticCode.GENERATED_IMAGE_REMOTE_ONLY_UNSUPPORTED:
        return (
            "Remote-only image result is not yet downloadable: "
            f"`{payload.get('source_uri', 'unknown')}`."
        )
    if fact.code == DiagnosticCode.GENERATED_IMAGE_RESOLUTION_MISMATCH:
        return (
            "Resolution mismatch: requested "
            f"`{payload.get('requested_resolution', 'unknown')}` "
            "but got "
            f"`{payload.get('actual_width', '?')}x{payload.get('actual_height', '?')}`."
        )
    if fact.code == DiagnosticCode.REQUESTED_RESOLUTION_UNSUPPORTED:
        supported = ", ".join(payload.get("supported_resolutions", []))
        return (
            "Requested resolution unsupported: "
            f"`{payload.get('requested_resolution', 'unknown')}`. "
            f"Supported: `{supported}`."
        )
    if fact.code == DiagnosticCode.RESPONSE_RECEIVED:
        image_count = payload.get("image_count", 0)
        elapsed_seconds = float(payload.get("elapsed_seconds", 0))
        return f"Result: {image_count} image(s) in {elapsed_seconds:.2f}s."
    if fact.code == DiagnosticCode.PROVIDER_ERROR:
        error_text = str(payload.get("error", "Provider request failed."))
        return f"Error: {shorten_error(error_text)}"
    return ""
