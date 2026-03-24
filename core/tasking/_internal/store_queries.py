"""Query helpers for the task store."""

from __future__ import annotations

from core.schemas import TaskManagerMetricsSnapshot, TaskSnapshot, TaskStatus

from .record import TaskRecord
from .store_support import snapshot_from_record


def get_snapshot(tasks: dict[str, TaskRecord], task_id: str) -> TaskSnapshot | None:
    """Return an immutable snapshot for a single task id."""
    record = tasks.get(task_id)
    return None if record is None else snapshot_from_record(record)


def list_snapshots(
    tasks: dict[str, TaskRecord],
    task_ids: list[str],
) -> list[TaskSnapshot]:
    """Return immutable snapshots in the same order as the input ids."""
    snapshots: list[TaskSnapshot] = []
    for task_id in task_ids:
        record = tasks.get(task_id)
        if record is not None:
            snapshots.append(snapshot_from_record(record))
    return snapshots


def metrics_snapshot(
    tasks: dict[str, TaskRecord],
    *,
    is_shutting_down: bool,
) -> TaskManagerMetricsSnapshot:
    """Summarize task counts for the admin dashboard."""
    status_counts: dict[str, int] = {}
    for record in tasks.values():
        status_counts[record.status.value] = status_counts.get(record.status.value, 0) + 1
    return TaskManagerMetricsSnapshot(
        queued_count=status_counts.get(TaskStatus.QUEUED.value, 0),
        running_count=status_counts.get(TaskStatus.RUNNING.value, 0),
        task_count=len(tasks),
        status_counts=status_counts,
        is_shutting_down=is_shutting_down,
    )


def has_running_tasks(tasks: dict[str, TaskRecord]) -> bool:
    """Return whether any task is currently in the running state."""
    return any(record.status == TaskStatus.RUNNING for record in tasks.values())
