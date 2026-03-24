"""Facade for all UI-facing interactions with the core runtime."""

from __future__ import annotations

from core._api_runtime import get_runtime
from core._api_ui_context import build_ui_context
from core._api_validation import (
    validate_divisible_by,
    validate_known_aspect_ratio,
    validate_task_config,
)
from core.schemas import (
    PreparedReferenceImage,
    TaskConfig,
    TaskId,
    TaskManagerMetricsSnapshot,
    TaskSnapshot,
    UIContext,
)
from core.tasking.entry import TaskSubmissionError


def initialize_runtime(config_path: str = "config.yaml", env_path: str = ".env") -> None:
    """
    INTENT: 初始化 facade 使用的运行时单例。
    INPUT:
        - config_path: 配置文件路径
        - env_path: 环境变量文件路径
    OUTPUT: None
    SIDE EFFECT: CONFIG_LOAD | BACKGROUND_THREAD_START
    FAILURE: 抛出配置加载或核心服务构造异常
    """
    from core._api_runtime import initialize_runtime as _initialize_runtime

    _initialize_runtime(config_path=config_path, env_path=env_path)


def get_ui_context() -> UIContext:
    """
    INTENT: 返回渲染界面和切换 provider 所需的只读上下文。
    INPUT: None
    OUTPUT: UIContext
    SIDE EFFECT: None
    FAILURE: 运行时未就绪或配置非法时抛出异常
    """
    runtime = get_runtime()
    return build_ui_context(runtime.config_manager)


def prepare_reference_image(
    raw_reference_image_path: str | None,
    divisible_by: int,
    aspect_ratio: str | None,
) -> PreparedReferenceImage | None:
    """
    INTENT: 校验预览输入并为 UI 准备参考图像。
    INPUT:
        - raw_reference_image_path: 原始参考图路径
        - divisible_by: 尺寸整除要求
        - aspect_ratio: 宽高比令牌
    OUTPUT: PreparedReferenceImage | None
    SIDE EFFECT: FILE_SYSTEM
    FAILURE: 输入非法时抛出 ValueError
    """
    runtime = get_runtime()
    validate_divisible_by(divisible_by)
    validate_known_aspect_ratio(build_ui_context(runtime.config_manager), aspect_ratio)
    return runtime.image_service.prepare_reference_image(
        raw_reference_image_path=raw_reference_image_path,
        divisible_by=divisible_by,
        aspect_ratio=aspect_ratio,
    )


def submit_generation_task(
    config: TaskConfig,
    owner_session_id: str | None = None,
) -> TaskId:
    """
    INTENT: 在 facade 边界校验生成任务并提交给任务管理器。
    INPUT:
        - config: UI 侧构造的 TaskConfig
        - owner_session_id: 可选的浏览器会话标识
    OUTPUT: TaskId
    SIDE EFFECT: BACKGROUND_QUEUE_WRITE | FILE_SYSTEM
    FAILURE: 输入非法时抛出 ValueError，入队失败时抛出 TaskSubmissionError
    """
    runtime = get_runtime()
    validated_config = validate_task_config(runtime.config_manager, config)
    return runtime.task_manager.submit(validated_config, owner_session_id=owner_session_id)


def list_tasks(task_ids: list[TaskId]) -> list[TaskSnapshot]:
    """
    INTENT: 按浏览器持有的任务 ID 顺序返回不可变任务快照。
    INPUT: task_ids - 有序任务 ID 列表
    OUTPUT: list[TaskSnapshot]
    SIDE EFFECT: None
    FAILURE: 运行时未就绪时抛出异常
    """
    runtime = get_runtime()
    return runtime.task_manager.list_tasks(task_ids)


def get_task_metrics() -> TaskManagerMetricsSnapshot:
    """
    INTENT: 向 UI 暴露当前任务管理器的运行指标。
    INPUT: None
    OUTPUT: TaskManagerMetricsSnapshot
    SIDE EFFECT: None
    FAILURE: 运行时未就绪时抛出异常
    """
    runtime = get_runtime()
    return runtime.task_manager.get_metrics_snapshot()


def begin_shutdown(
    reason: str = "Task manager is shutting down. Please try again later."
) -> None:
    """
    INTENT: 请求后台任务执行进入优雅关闭流程。
    INPUT: reason - 面向用户的关闭原因
    OUTPUT: None
    SIDE EFFECT: BACKGROUND_THREAD_SIGNAL
    FAILURE: 运行时未就绪时抛出异常
    """
    runtime = get_runtime()
    runtime.task_manager.begin_shutdown(reason=reason)
    runtime.task_manager.close()


__all__ = [
    "TaskSubmissionError",
    "begin_shutdown",
    "get_task_metrics",
    "get_ui_context",
    "initialize_runtime",
    "list_tasks",
    "prepare_reference_image",
    "submit_generation_task",
]
