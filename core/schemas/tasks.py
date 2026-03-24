"""Public task orchestration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import TypedDict

from core.schemas.enums import TaskErrorCode, TaskStatus
from core.schemas.ids import TaskId
from core.schemas.service import GenerationResult, ProviderDiagnostics


class BrowserTaskStateValue(TypedDict):
    """Serialized browser-owned task state stored in Gradio state."""

    task_ids: list[TaskId]
    selected_task_id: TaskId | None


@dataclass(frozen=True)
class TaskManagerSettings:
    """Runtime settings for the in-memory task manager."""

    max_running_tasks: int = 2
    max_pending_tasks: int = 20
    task_ttl_seconds: int = 10800
    running_timeout_seconds: int = 3600
    cleanup_interval_seconds: int = 600
    shutdown_drain_timeout_seconds: int = 10


@dataclass(frozen=True)
class TaskManagerMetricsSnapshot:
    """Operational metrics derived from the in-memory task store."""

    queued_count: int = 0
    running_count: int = 0
    task_count: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    is_shutting_down: bool = False


@dataclass(frozen=True)
class TaskSnapshot:
    """UI-facing immutable task view."""

    task_id: TaskId
    status: TaskStatus
    provider: str
    model: str
    prompt_preview: str
    submitted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    result: GenerationResult | None = None
    error: str | None = None
    error_code: TaskErrorCode | None = None
    diagnostics: ProviderDiagnostics | None = None
    prepared_reference_image_path: str | None = None
    related_files: list[str] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal


@dataclass(frozen=True)
class BrowserTaskState:
    """Browser-local task ids persisted across refreshes."""

    task_ids: list[TaskId] = field(default_factory=list)
    selected_task_id: TaskId | None = None

    @staticmethod
    def from_value(value: "BrowserTaskState | BrowserTaskStateValue | object") -> "BrowserTaskState":
        if isinstance(value, BrowserTaskState):
            return value
        if not isinstance(value, dict):
            return BrowserTaskState()
        task_ids = value.get("task_ids", [])
        selected_task_id = value.get("selected_task_id")
        normalized_ids = [
            str(task_id)
            for task_id in task_ids
            if isinstance(task_id, (str, int)) and str(task_id).strip()
        ]
        normalized_selected = (
            str(selected_task_id).strip()
            if isinstance(selected_task_id, (str, int)) and str(selected_task_id).strip()
            else None
        )
        return BrowserTaskState(
            task_ids=normalized_ids,
            selected_task_id=normalized_selected,
        )

    def to_value(self) -> BrowserTaskStateValue:
        return {
            "task_ids": list(self.task_ids),
            "selected_task_id": self.selected_task_id,
        }

    def with_task(self, task_id: TaskId, *, max_items: int = 20) -> "BrowserTaskState":
        deduped = [task_id] + [value for value in self.task_ids if value != task_id]
        return replace(
            self,
            task_ids=deduped[:max_items],
            selected_task_id=task_id,
        )
