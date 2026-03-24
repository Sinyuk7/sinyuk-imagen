"""Status-bar formatting helpers for generation output."""

from __future__ import annotations

from core.schemas import DiagnosticCode, ProviderDiagnostics, TaskErrorCode


def build_success_status(
    image_count: int,
    elapsed_seconds: float,
    provider: str,
    model: str,
    diagnostics: ProviderDiagnostics | None = None,
) -> str:
    """Build the status bar text for successful generations."""
    top_line = f"**{image_count} image(s)** in `{elapsed_seconds:.2f}s`"
    detail_line = f"`{provider}` | `{model}`"
    lines = [top_line, detail_line, *build_resolution_warning_lines(diagnostics)]
    return "  \n".join(lines)


def build_error_status(
    error_message: str,
    error_code: TaskErrorCode | None = None,
) -> str:
    """Build the status bar text for failed generations."""
    title = error_title(error_code)
    return f"**{title}**  \n{shorten_error(error_message)}"


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
