"""Pure helpers for task store state handling."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from core.schemas import TaskSnapshot, TaskStatus

from .record import TaskRecord


@dataclass(frozen=True)
class StartAttemptResult:
    """Result of claiming a task execution lease."""

    attempt_id: int | None = None
    cleanup_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExpiredTaskCleanup:
    """Files and task ids collected during watchdog cleanup."""

    paths_to_cleanup: list[str] = field(default_factory=list)
    expired_task_ids: list[str] = field(default_factory=list)


def build_prompt_preview(prompt: str) -> str:
    """Build the stable task prompt preview shown in UI snapshots."""
    preview = " ".join(prompt.split())[:80]
    return preview or "(empty prompt)"


def snapshot_from_record(record: TaskRecord) -> TaskSnapshot:
    """Build an immutable UI snapshot from a mutable task record."""
    return TaskSnapshot(
        task_id=record.task_id,
        status=record.status,
        provider=record.provider,
        model=record.model,
        prompt_preview=record.prompt_preview,
        submitted_at=record.submitted_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        elapsed_seconds=record.elapsed_seconds,
        result=deepcopy(record.result),
        error=record.error,
        error_code=record.error_code,
        diagnostics=deepcopy(record.diagnostics),
        prepared_reference_image_path=record.prepared_reference_image_path,
        related_files=list(record.related_files),
    )


def elapsed_seconds(record: TaskRecord, finished_at: datetime) -> float | None:
    """Compute elapsed runtime for a task when both timestamps are known."""
    if record.started_at is None:
        return None
    return round((finished_at - record.started_at).total_seconds(), 2)


def should_timeout(record: TaskRecord, now: datetime, timeout_window: timedelta) -> bool:
    """Return whether a running task has exceeded the configured timeout."""
    return (
        record.status == TaskStatus.RUNNING
        and record.started_at is not None
        and now - record.started_at > timeout_window
    )


def is_ttl_expired(record: TaskRecord, now: datetime, ttl_window: timedelta) -> bool:
    """Return whether a terminal task record should be evicted from memory."""
    if not record.status.is_terminal:
        return False
    terminal_time = record.finished_at or record.submitted_at
    return now - terminal_time > ttl_window
