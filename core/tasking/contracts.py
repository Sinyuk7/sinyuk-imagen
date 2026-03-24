"""
core/tasking/contracts - 任务管理模块的公开类型契约

INTENT:
    定义 tasking 模块与外部交互的所有类型契约。
    这些类型是稳定的公开 API。

SIDE EFFECT: None (纯类型定义)
"""

from dataclasses import dataclass, field
from typing import TypeAlias

from core.schemas.enums import TaskStatus, TaskErrorCode

TaskParams: TypeAlias = dict[str, object]


@dataclass(frozen=True)
class TaskSubmission:
    """
    任务提交请求

    INTENT: 封装提交新任务所需的全部参数
    """

    provider_id: str
    model_id: str
    prompt: str
    params: TaskParams = field(default_factory=dict)
    reference_image_path: str | None = None
    owner_session_id: str | None = None


@dataclass(frozen=True)
class TaskResult:
    """
    任务结果快照

    INTENT: 封装任务的当前状态和结果
    """

    task_id: str
    status: TaskStatus
    provider: str
    model: str
    prompt_preview: str
    images: list[str] = field(default_factory=list)
    error_code: TaskErrorCode | None = None
    error_message: str | None = None
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class TaskMetrics:
    """
    任务管理器指标

    INTENT: 封装任务管理器的运行状态概览
    """

    queued_count: int = 0
    running_count: int = 0
    total_count: int = 0
    is_shutting_down: bool = False
