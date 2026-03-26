"""Status-bar formatting helpers for generation output."""

from __future__ import annotations

from html import escape

from core.schemas import DiagnosticCode, ProviderDiagnostics, TaskErrorCode

STATUS_CARD_STYLE = """
<style>
#generation-status-bar .generation-status-card {
  display: grid;
  gap: 0.42rem;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid var(--block-border-color, var(--neutral-200));
  background: var(--background-fill-secondary, var(--neutral-50));
  color: var(--body-text-color);
}
#generation-status-bar .generation-status-card.status-neutral {
  border-color: var(--block-border-color, var(--neutral-200));
}
#generation-status-bar .generation-status-card.status-info {
  border-color: color-mix(in srgb, var(--primary-400) 40%, var(--block-border-color, white) 60%);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 80%, var(--primary-100) 20%);
}
#generation-status-bar .generation-status-card.status-success {
  border-color: color-mix(in srgb, var(--color-green-400, #4ade80) 42%, var(--block-border-color, white) 58%);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 78%, var(--color-green-100, #dcfce7) 22%);
}
#generation-status-bar .generation-status-card.status-error {
  border-color: color-mix(in srgb, var(--color-red-400, #fb7185) 42%, var(--block-border-color, white) 58%);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 76%, var(--color-red-100, #ffe4e6) 24%);
}
#generation-status-bar .generation-status-card.status-warning {
  border-color: color-mix(in srgb, var(--color-amber-400, #f59e0b) 42%, var(--block-border-color, white) 58%);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 78%, var(--color-amber-100, #fef3c7) 22%);
}
#generation-status-bar .generation-status-eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--body-text-color-subdued, var(--neutral-500));
}
#generation-status-bar .generation-status-title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.35;
}
#generation-status-bar .generation-status-summary {
  font-size: 0.94rem;
  line-height: 1.45;
}
#generation-status-bar .generation-status-meta {
  font-size: 0.84rem;
  color: var(--body-text-color-subdued, var(--neutral-500));
}
#generation-status-bar .generation-status-list {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.22rem;
}
</style>
"""


def build_empty_status(message: str) -> str:
    """Build the status card shown before any task is selected."""
    return _build_status_card(
        tone="neutral",
        eyebrow="Preview",
        title="No task selected yet",
        summary=message,
    )


def build_info_status(
    *,
    eyebrow: str,
    title: str,
    summary: str,
    detail_lines: list[str] | None = None,
    tone: str = "info",
) -> str:
    """Build a neutral or informational status card."""
    return _build_status_card(
        tone=tone,
        eyebrow=eyebrow,
        title=title,
        summary=summary,
        detail_lines=detail_lines,
    )


def build_success_status(
    image_count: int,
    elapsed_seconds: float,
    provider: str,
    model: str,
    diagnostics: ProviderDiagnostics | None = None,
) -> str:
    """Build the status bar text for successful generations."""
    warning_lines = build_resolution_warning_lines(diagnostics)
    return _build_status_card(
        tone="success",
        eyebrow="Success",
        title=f"{image_count} image(s) ready in {elapsed_seconds:.2f}s",
        summary="These images are available in this session now. Download them before leaving if you want to keep them.",
        detail_lines=[f"{provider} · {model}", *warning_lines],
    )


def build_error_status(
    error_message: str,
    error_code: TaskErrorCode | None = None,
) -> str:
    """Build the status bar text for failed generations."""
    title = error_title(error_code)
    summary = explain_error(error_message, error_code)
    tone = "warning" if error_code == TaskErrorCode.TIMED_OUT else "error"
    return _build_status_card(
        tone=tone,
        eyebrow="Needs attention",
        title=title,
        summary=summary,
        detail_lines=["Open details below if you need the technical error."],
    )


def error_title(error_code: TaskErrorCode | None) -> str:
    """Resolve a human-facing title for a task error code."""
    if error_code is None:
        return "Generation failed"
    return {
        TaskErrorCode.INVALID_REQUEST: "Request invalid",
        TaskErrorCode.QUEUE_FULL: "Queue full",
        TaskErrorCode.SHUTDOWN: "Shutting down",
        TaskErrorCode.INPUT_MATERIALIZATION_FAILED: "Input staging failed",
        TaskErrorCode.RESULT_MATERIALIZATION_FAILED: "Result staging failed",
        TaskErrorCode.PROVIDER_ERROR: "Generation failed",
        TaskErrorCode.TIMED_OUT: "Task timed out",
    }.get(error_code, "Generation failed")


def shorten_error(error_message: str, max_length: int = 180) -> str:
    """Collapse whitespace and clamp long provider errors."""
    cleaned = " ".join(error_message.split())
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 3].rstrip()}..."


def explain_error(
    error_message: str,
    error_code: TaskErrorCode | None = None,
) -> str:
    """Map technical failures into short user-facing explanations."""
    cleaned = shorten_error(error_message)
    lowered = cleaned.lower()

    if error_code == TaskErrorCode.QUEUE_FULL:
        return "Too many image tasks are already waiting or running. Please try again in a moment."
    if error_code == TaskErrorCode.SHUTDOWN:
        return "The app is shutting down, so this task could not continue."
    if error_code == TaskErrorCode.INPUT_MATERIALIZATION_FAILED:
        return "We could not prepare your input files for this request."
    if error_code == TaskErrorCode.RESULT_MATERIALIZATION_FAILED:
        return "The provider finished, but the images could not be prepared for download."
    if error_code == TaskErrorCode.TIMED_OUT or "timed out" in lowered or "timeout" in lowered:
        return "The provider took too long to respond. You can try again."

    if any(token in lowered for token in ("401", "403", "unauthorized", "forbidden", "invalid api key", "api key")):
        return "Your API key looks invalid, missing, or does not have permission for this request."
    if any(token in lowered for token in ("rate limit", "quota", "429", "too many requests")):
        return "The provider is rate-limiting this request right now. Please wait and try again."
    if any(token in lowered for token in ("connection", "network", "dns", "socket", "temporarily unavailable")):
        return "We could not reach the provider reliably. Please check your network or try again."
    if any(token in lowered for token in ("500", "502", "503", "504", "server error", "internal error", "bad gateway")):
        return "The provider is temporarily unavailable. Please try again later."
    if error_code == TaskErrorCode.INVALID_REQUEST:
        return "This request could not be sent as-is. Please check the prompt, image, or advanced parameters."

    return "The provider could not complete this image request. Open details below if you need the technical error."


def build_resolution_warning_lines(
    diagnostics: ProviderDiagnostics | None,
) -> list[str]:
    """Collect human-facing warning lines for the status bar."""
    if not diagnostics:
        return []

    warning_lines: list[str] = []
    for fact in diagnostics.facts:
        if fact.code != DiagnosticCode.GENERATED_IMAGE_RESOLUTION_MISMATCH:
            continue
        payload = fact.payload
        warning_lines.append(
            "Warning: requested "
            f"`{payload.get('requested_resolution', 'unknown')}` "
            "but received "
            f"`{payload.get('actual_width', '?')}x{payload.get('actual_height', '?')}`."
        )
    return warning_lines


def _build_status_card(
    *,
    tone: str,
    eyebrow: str,
    title: str,
    summary: str,
    detail_lines: list[str] | None = None,
) -> str:
    """Render a themed HTML status card for the output panel."""
    safe_detail_lines = [line for line in (detail_lines or []) if line]
    details_html = ""
    if safe_detail_lines:
        escaped_lines = "".join(
            f"<li>{escape(line)}</li>"
            for line in safe_detail_lines
        )
        details_html = f'<ul class="generation-status-list">{escaped_lines}</ul>'
    return (
        STATUS_CARD_STYLE
        + f'<div class="generation-status-card status-{escape(tone)}">'
        + f'<div class="generation-status-eyebrow">{escape(eyebrow)}</div>'
        + f'<div class="generation-status-title">{escape(title)}</div>'
        + f'<div class="generation-status-summary">{escape(summary)}</div>'
        + f"{details_html}"
        + "</div>"
    )
