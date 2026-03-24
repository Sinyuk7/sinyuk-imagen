"""Lifecycle helpers for the task store."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta

from core.schemas import (
    GenerationResult,
    TaskConfig,
    TaskErrorCode,
    TaskStatus,
)

from .exceptions import InvalidTaskTransition
from .record import TaskRecord
from .store_support import (
    ExpiredTaskCleanup,
    StartAttemptResult,
    build_prompt_preview,
    elapsed_seconds,
    is_ttl_expired,
    should_timeout,
)
from .store_terminal import ensure_running, finish_for_shutdown, set_terminal_state


def create_task(
    tasks: dict[str, TaskRecord],
    task_id: str,
    task_config: TaskConfig,
    *,
    owner_session_id: str | None,
    now: datetime,
    related_files: list[str],
    max_pending_tasks: int,
    is_shutting_down: bool,
    shutdown_reason: str,
) -> None:
    """Create a new queued task record."""
    if is_shutting_down:
        raise ValueError(shutdown_reason)
    pending_count = sum(1 for record in tasks.values() if not record.status.is_terminal)
    if pending_count >= max_pending_tasks:
        raise ValueError("Task queue is full. Please wait for running tasks to finish.")
    tasks[task_id] = TaskRecord(
        task_id=task_id,
        owner_session_id=owner_session_id,
        provider=task_config.provider,
        model=task_config.model,
        prompt_preview=build_prompt_preview(task_config.prompt),
        submitted_at=now,
        status=TaskStatus.QUEUED,
        related_files=list(related_files),
    )


def mark_preparing(tasks: dict[str, TaskRecord], task_id: str) -> bool:
    """Transition a queued task into preparing."""
    record = tasks.get(task_id)
    if record is None or record.status.is_terminal:
        return False
    if record.status != TaskStatus.QUEUED:
        raise InvalidTaskTransition(
            f"Only queued tasks can enter preparing, got {record.status.value}."
        )
    record.status = TaskStatus.PREPARING
    return True


def start_attempt(
    tasks: dict[str, TaskRecord],
    task_id: str,
    *,
    now: datetime,
    shutdown_reason: str | None = None,
) -> StartAttemptResult:
    """Claim a running attempt for a task if it is still eligible."""
    record = tasks.get(task_id)
    if record is None or record.status.is_terminal:
        return StartAttemptResult()
    if shutdown_reason is not None:
        if record.status in {TaskStatus.QUEUED, TaskStatus.PREPARING}:
            cleanup_paths = finish_for_shutdown(record, now, shutdown_reason)
            return StartAttemptResult(cleanup_paths=cleanup_paths)
        return StartAttemptResult()
    if record.status != TaskStatus.PREPARING:
        raise InvalidTaskTransition(
            f"Only preparing tasks can start running, got {record.status.value}."
        )

    record.status = TaskStatus.RUNNING
    record.started_at = now
    record.finished_at = None
    record.elapsed_seconds = None
    record.error = None
    record.error_code = None
    record.result = None
    record.diagnostics = None
    record.attempt_id += 1
    return StartAttemptResult(attempt_id=record.attempt_id)


def finish_failure(
    tasks: dict[str, TaskRecord],
    task_id: str,
    *,
    attempt_id: int,
    now: datetime,
    error_message: str,
    error_code: TaskErrorCode,
) -> None:
    """Fail the active running attempt."""
    record = tasks.get(task_id)
    if record is None or record.attempt_id != attempt_id or record.status.is_terminal:
        return
    ensure_running(record, action="fail")
    set_terminal_state(
        record,
        status=TaskStatus.FAILED,
        now=now,
        error=error_message,
        error_code=error_code,
        result=None,
        clear_related_files=False,
        prepared_reference_image_path=record.prepared_reference_image_path,
        diagnostics=record.diagnostics,
    )


def finish_timeout(
    tasks: dict[str, TaskRecord],
    task_id: str,
    *,
    attempt_id: int,
    now: datetime,
    error_message: str,
) -> list[str]:
    """Mark the active running attempt as timed out."""
    record = tasks.get(task_id)
    if record is None or record.attempt_id != attempt_id or record.status.is_terminal:
        return []
    ensure_running(record, action="time out")
    return set_terminal_state(
        record,
        status=TaskStatus.TIMED_OUT,
        now=now,
        error=error_message,
        error_code=TaskErrorCode.TIMED_OUT,
        result=None,
        clear_related_files=True,
        prepared_reference_image_path=None,
        diagnostics=record.diagnostics,
    )


def finish_success(
    tasks: dict[str, TaskRecord],
    task_id: str,
    *,
    attempt_id: int,
    now: datetime,
    result: GenerationResult,
    result_paths: list[str],
) -> list[str]:
    """Commit a successful or failed provider result into the task record."""
    record = tasks.get(task_id)
    if record is None or record.attempt_id != attempt_id or record.status.is_terminal:
        return list(result_paths)
    ensure_running(record, action="complete")
    for path in result_paths:
        if path not in record.related_files:
            record.related_files.append(path)
    record.result = result
    record.diagnostics = deepcopy(result.diagnostics)
    record.prepared_reference_image_path = result.prepared_reference_image_path
    record.finished_at = now
    record.elapsed_seconds = elapsed_seconds(record, now)
    record.error = result.error
    record.error_code = None
    record.status = TaskStatus.SUCCEEDED if result.success else TaskStatus.FAILED
    return []


def fail_pending_for_shutdown(
    tasks: dict[str, TaskRecord],
    *,
    now: datetime,
    reason: str,
) -> list[str]:
    """Fail all queued or preparing tasks because the runtime is shutting down."""
    cleanup_paths: list[str] = []
    for record in tasks.values():
        if record.status in {TaskStatus.QUEUED, TaskStatus.PREPARING}:
            cleanup_paths.extend(finish_for_shutdown(record, now, reason))
    return cleanup_paths


def fail_task_for_shutdown(
    tasks: dict[str, TaskRecord],
    task_id: str,
    *,
    now: datetime,
    reason: str,
) -> list[str]:
    """Fail a single non-running task because the runtime is shutting down."""
    record = tasks.get(task_id)
    if record is None or record.status.is_terminal or record.status == TaskStatus.RUNNING:
        return []
    return finish_for_shutdown(record, now, reason)


def collect_expired(
    tasks: dict[str, TaskRecord],
    *,
    now: datetime,
    running_timeout_seconds: int,
    task_ttl_seconds: int,
) -> ExpiredTaskCleanup:
    """Collect cleanup work for timed-out or TTL-expired tasks."""
    expired_ids: list[str] = []
    cleanup_paths: list[str] = []
    timeout_window = timedelta(seconds=running_timeout_seconds)
    ttl_window = timedelta(seconds=task_ttl_seconds)
    for task_id, record in tasks.items():
        if should_timeout(record, now, timeout_window):
            cleanup_paths.extend(
                set_terminal_state(
                    record,
                    status=TaskStatus.TIMED_OUT,
                    now=now,
                    error="Task execution timed out.",
                    error_code=TaskErrorCode.TIMED_OUT,
                    result=None,
                    clear_related_files=True,
                    prepared_reference_image_path=None,
                    diagnostics=record.diagnostics,
                )
            )
        if is_ttl_expired(record, now, ttl_window):
            expired_ids.append(task_id)
    return ExpiredTaskCleanup(paths_to_cleanup=cleanup_paths, expired_task_ids=expired_ids)


def delete_task(tasks: dict[str, TaskRecord], task_id: str) -> list[str]:
    """Delete a task record and return its related files for cleanup."""
    record = tasks.pop(task_id, None)
    return [] if record is None else list(record.related_files)
