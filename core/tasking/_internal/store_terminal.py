"""Terminal-state helpers for the task store."""

from __future__ import annotations

from datetime import datetime

from core.schemas import (
    GenerationResult,
    ProviderDiagnostics,
    TaskErrorCode,
    TaskStatus,
)

from .exceptions import InvalidTaskTransition
from .record import TaskRecord
from .store_support import elapsed_seconds


def finish_for_shutdown(
    record: TaskRecord,
    now: datetime,
    reason: str,
) -> list[str]:
    """Fail a queued or preparing task because the runtime is shutting down."""
    return set_terminal_state(
        record,
        status=TaskStatus.FAILED,
        now=now,
        error=reason,
        error_code=TaskErrorCode.SHUTDOWN,
        result=None,
        clear_related_files=True,
        prepared_reference_image_path=None,
        diagnostics=None,
    )


def set_terminal_state(
    record: TaskRecord,
    *,
    status: TaskStatus,
    now: datetime,
    error: str | None,
    error_code: TaskErrorCode | None,
    result: GenerationResult | None,
    clear_related_files: bool,
    prepared_reference_image_path: str | None,
    diagnostics: ProviderDiagnostics | None,
) -> list[str]:
    """Apply the final terminal fields to a task record."""
    cleanup_paths: list[str] = []
    if clear_related_files:
        cleanup_paths = list(record.related_files)
        record.related_files = []
    record.status = status
    record.finished_at = now
    record.elapsed_seconds = elapsed_seconds(record, now)
    record.error = error
    record.error_code = error_code
    record.result = result
    record.saved_at = None
    record.diagnostics = diagnostics
    record.prepared_reference_image_path = prepared_reference_image_path
    return cleanup_paths


def ensure_running(record: TaskRecord, *, action: str) -> None:
    """Reject transitions that require a running task."""
    if record.status != TaskStatus.RUNNING:
        raise InvalidTaskTransition(
            f"Only running tasks can {action}, got {record.status.value}."
        )
