"""Private task state store and lifecycle rules."""

from __future__ import annotations

from datetime import datetime
import threading

from core.schemas import (
    GenerationResult,
    TaskConfig,
    TaskErrorCode,
    TaskManagerMetricsSnapshot,
    TaskSnapshot,
)

from .record import TaskRecord
from .store_lifecycle import (
    collect_expired,
    create_task,
    delete_task,
    fail_pending_for_shutdown,
    fail_task_for_shutdown,
    finish_failure,
    finish_success,
    finish_timeout,
    mark_preparing,
    start_attempt,
)
from .store_queries import (
    get_snapshot,
    has_running_tasks,
    list_snapshots,
    metrics_snapshot,
)
from .store_support import ExpiredTaskCleanup, StartAttemptResult


class TaskStore:
    """Own task records and lifecycle transitions behind a lock."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = threading.RLock()

    def create_task(
        self,
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
        with self._lock:
            create_task(
                self._tasks,
                task_id,
                task_config,
                owner_session_id=owner_session_id,
                now=now,
                related_files=related_files,
                max_pending_tasks=max_pending_tasks,
                is_shutting_down=is_shutting_down,
                shutdown_reason=shutdown_reason,
            )

    def get_snapshot(self, task_id: str) -> TaskSnapshot | None:
        with self._lock:
            return get_snapshot(self._tasks, task_id)

    def list_snapshots(self, task_ids: list[str]) -> list[TaskSnapshot]:
        with self._lock:
            return list_snapshots(self._tasks, task_ids)

    def metrics_snapshot(self, *, is_shutting_down: bool) -> TaskManagerMetricsSnapshot:
        with self._lock:
            return metrics_snapshot(self._tasks, is_shutting_down=is_shutting_down)

    def mark_preparing(self, task_id: str) -> bool:
        with self._lock:
            return mark_preparing(self._tasks, task_id)

    def start_attempt(
        self,
        task_id: str,
        *,
        now: datetime,
        shutdown_reason: str | None = None,
    ) -> StartAttemptResult:
        with self._lock:
            return start_attempt(
                self._tasks,
                task_id,
                now=now,
                shutdown_reason=shutdown_reason,
            )

    def finish_failure(
        self,
        task_id: str,
        *,
        attempt_id: int,
        now: datetime,
        error_message: str,
        error_code: TaskErrorCode,
    ) -> None:
        with self._lock:
            finish_failure(
                self._tasks,
                task_id,
                attempt_id=attempt_id,
                now=now,
                error_message=error_message,
                error_code=error_code,
            )

    def finish_timeout(
        self,
        task_id: str,
        *,
        attempt_id: int,
        now: datetime,
        error_message: str,
    ) -> list[str]:
        with self._lock:
            return finish_timeout(
                self._tasks,
                task_id,
                attempt_id=attempt_id,
                now=now,
                error_message=error_message,
            )

    def finish_success(
        self,
        task_id: str,
        *,
        attempt_id: int,
        now: datetime,
        result: GenerationResult,
        result_paths: list[str],
    ) -> list[str]:
        with self._lock:
            return finish_success(
                self._tasks,
                task_id,
                attempt_id=attempt_id,
                now=now,
                result=result,
                result_paths=result_paths,
            )

    def fail_pending_for_shutdown(self, *, now: datetime, reason: str) -> list[str]:
        with self._lock:
            return fail_pending_for_shutdown(self._tasks, now=now, reason=reason)

    def fail_task_for_shutdown(self, task_id: str, *, now: datetime, reason: str) -> list[str]:
        with self._lock:
            return fail_task_for_shutdown(self._tasks, task_id, now=now, reason=reason)

    def collect_expired(
        self,
        *,
        now: datetime,
        running_timeout_seconds: int,
        task_ttl_seconds: int,
    ) -> ExpiredTaskCleanup:
        with self._lock:
            return collect_expired(
                self._tasks,
                now=now,
                running_timeout_seconds=running_timeout_seconds,
                task_ttl_seconds=task_ttl_seconds,
            )

    def delete_task(self, task_id: str) -> list[str]:
        with self._lock:
            return delete_task(self._tasks, task_id)

    def has_running_tasks(self) -> bool:
        with self._lock:
            return has_running_tasks(self._tasks)
