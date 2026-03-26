"""Internal mutable task record owned by the task store."""

from dataclasses import dataclass, field
from datetime import datetime

from core.schemas import GenerationResult, ProviderDiagnostics, TaskErrorCode, TaskStatus


@dataclass
class TaskRecord:
    """Internal mutable task record managed by TaskManager."""

    task_id: str
    owner_session_id: str | None
    provider: str
    model: str
    prompt_preview: str
    submitted_at: datetime
    status: TaskStatus = TaskStatus.QUEUED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    error: str | None = None
    error_code: TaskErrorCode | None = None
    result: GenerationResult | None = None
    saved_at: datetime | None = None
    diagnostics: ProviderDiagnostics | None = None
    prepared_reference_image_path: str | None = None
    related_files: list[str] = field(default_factory=list)
    attempt_id: int = 0
