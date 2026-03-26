"""
core/tasking/entry - 任务管理模块入口

INTENT:
    提供任务管理功能的公开入口函数和类。
    这些是外部调用 tasking 模块的唯一合法路径。

SIDE EFFECT: 内部状态管理
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Iterable, Optional, TYPE_CHECKING

from core.schemas import (
    TaskConfig,
    TaskErrorCode,
    TaskManagerMetricsSnapshot,
    TaskManagerSettings,
    TaskSnapshot,
)
from core.tasking._internal.artifacts import TaskArtifactStore
from core.tasking._internal.policies import ProviderConcurrencyPolicy
from core.tasking._internal.runtime import TaskRuntime
from core.tasking._internal.store import TaskStore

if TYPE_CHECKING:
    from core.generation.entry import ImageGenerationService


class TaskSubmissionError(Exception):
    """
    任务提交错误

    INTENT: 表示任务提交失败
    """

    def __init__(self, code: TaskErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TaskManager:
    """
    任务管理器

    INTENT: 应用级异步任务管理器，提供稳定的公开契约
    SIDE EFFECT: 内部状态管理 (任务队列、运行状态)
    """

    def __init__(
        self,
        image_service: "ImageGenerationService",
        *,
        settings: Optional[TaskManagerSettings] = None,
    ) -> None:
        """
        初始化任务管理器

        INTENT: 创建任务管理器实例
        INPUT:
            - image_service: 图像生成服务
            - settings: 可选的管理器配置
        OUTPUT: TaskManager 实例
        SIDE EFFECT: 启动后台工作线程
        FAILURE: 无
        """
        self._settings = settings or TaskManagerSettings()
        self._store = TaskStore()
        self._artifact_store = TaskArtifactStore()
        self._provider_policy = ProviderConcurrencyPolicy.from_config_manager(
            getattr(image_service, "_config", None)
        )
        self._runtime = TaskRuntime(
            image_service=image_service,
            store=self._store,
            artifact_store=self._artifact_store,
            settings=self._settings,
            provider_policy=self._provider_policy,
        )

    def submit(
        self,
        task_config: TaskConfig,
        *,
        owner_session_id: Optional[str] = None,
    ) -> str:
        """
        提交任务

        INTENT: 提交一个任务并立即返回任务 ID
        INPUT:
            - task_config: 任务配置
            - owner_session_id: 可选的会话 ID
        OUTPUT: 任务 ID
        SIDE EFFECT: 任务入队
        FAILURE: 抛出 TaskSubmissionError
        """
        task_id = uuid.uuid4().hex
        try:
            prepared_inputs = self._artifact_store.prepare_task_inputs(task_id, task_config)
        except Exception as exc:
            self._artifact_store.delete_task(task_id, [])
            raise TaskSubmissionError(
                TaskErrorCode.INPUT_MATERIALIZATION_FAILED,
                f"Failed to stage task inputs: {exc}",
            ) from exc

        try:
            self._store.create_task(
                task_id,
                prepared_inputs.task_config,
                owner_session_id=owner_session_id,
                now=self._utcnow(),
                related_files=prepared_inputs.related_files,
                max_pending_tasks=self._settings.max_pending_tasks,
                is_shutting_down=self._runtime.is_shutting_down(),
                shutdown_reason=self._runtime.shutdown_reason,
            )
        except ValueError as exc:
            self._artifact_store.delete_task(task_id, prepared_inputs.related_files)
            raise self._build_submission_error(exc) from exc

        self._runtime.enqueue_task(task_id, prepared_inputs.task_config)
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskSnapshot]:
        """
        获取任务状态

        INTENT: 返回不可变的任务快照
        INPUT: task_id - 任务 ID
        OUTPUT: TaskSnapshot 或 None
        SIDE EFFECT: None
        FAILURE: 返回 None
        """
        return self._store.get_snapshot(task_id)

    def list_tasks(self, task_ids: Iterable[str]) -> list[TaskSnapshot]:
        """
        批量获取任务状态

        INTENT: 按提供的顺序返回任务快照，跳过不存在的 ID
        INPUT: task_ids - 任务 ID 列表
        OUTPUT: TaskSnapshot 列表
        SIDE EFFECT: None
        FAILURE: 返回空列表
        """
        return self._store.list_snapshots(list(task_ids))

    def list_tasks_for_session(self, owner_session_id: str) -> list[TaskSnapshot]:
        """
        INTENT: 按页面会话返回该会话拥有的任务快照。
        INPUT:
            - owner_session_id: 当前页面会话 ID
        OUTPUT: list[TaskSnapshot]
        SIDE EFFECT: 更新会话最近访问时间
        FAILURE: owner_session_id 为空时抛出 ValueError
        """
        if not owner_session_id.strip():
            raise ValueError("Page session id is required.")
        now = self._utcnow()
        self._store.touch_session(owner_session_id, now=now)
        return self._store.list_snapshots_for_session(owner_session_id)

    def touch_session(self, owner_session_id: str) -> None:
        """
        INTENT: 刷新页面会话的最近访问时间。
        INPUT:
            - owner_session_id: 当前页面会话 ID
        OUTPUT: None
        SIDE EFFECT: 更新会话最近访问时间
        FAILURE: owner_session_id 为空时抛出 ValueError
        """
        if not owner_session_id.strip():
            raise ValueError("Page session id is required.")
        self._store.touch_session(owner_session_id, now=self._utcnow())

    def has_unsaved_outputs_for_session(self, owner_session_id: str) -> bool:
        """
        INTENT: 判断页面会话是否仍有未标记保存的成功结果。
        INPUT:
            - owner_session_id: 当前页面会话 ID
        OUTPUT: bool
        SIDE EFFECT: 更新会话最近访问时间
        FAILURE: owner_session_id 为空时抛出 ValueError
        """
        if not owner_session_id.strip():
            raise ValueError("Page session id is required.")
        self._store.touch_session(owner_session_id, now=self._utcnow())
        return self._store.has_unsaved_outputs_for_session(owner_session_id)

    def mark_task_saved(self, task_id: str, *, owner_session_id: str) -> None:
        """
        INTENT: 将成功任务显式标记为已保存。
        INPUT:
            - task_id: 任务 ID
            - owner_session_id: 当前页面会话 ID
        OUTPUT: None
        SIDE EFFECT: 更新任务保存状态与会话最近访问时间
        FAILURE: task_id 或 owner_session_id 非法时抛出 ValueError
        """
        if not task_id.strip():
            raise ValueError("Task id is required.")
        if not owner_session_id.strip():
            raise ValueError("Page session id is required.")
        now = self._utcnow()
        self._store.touch_session(owner_session_id, now=now)
        self._store.mark_task_saved(
            task_id,
            owner_session_id=owner_session_id,
            now=now,
        )

    def mark_all_tasks_saved(self, *, owner_session_id: str) -> int:
        """
        INTENT: 将当前页面会话下所有成功任务标记为已保存。
        INPUT:
            - owner_session_id: 当前页面会话 ID
        OUTPUT: int
        SIDE EFFECT: 更新多个任务保存状态与会话最近访问时间
        FAILURE: owner_session_id 非法时抛出 ValueError
        """
        if not owner_session_id.strip():
            raise ValueError("Page session id is required.")
        now = self._utcnow()
        self._store.touch_session(owner_session_id, now=now)
        return self._store.mark_all_tasks_saved(
            owner_session_id=owner_session_id,
            now=now,
        )

    def get_metrics_snapshot(self) -> TaskManagerMetricsSnapshot:
        """
        获取指标快照

        INTENT: 返回任务存储的运行状态概览
        INPUT: None
        OUTPUT: TaskManagerMetricsSnapshot
        SIDE EFFECT: None
        FAILURE: 无
        """
        return self._store.metrics_snapshot(is_shutting_down=self._runtime.is_shutting_down())

    def begin_shutdown(
        self,
        *,
        reason: str = "Task manager is shutting down. Please try again later.",
    ) -> None:
        """
        开始关闭

        INTENT: 阻止新任务并使未开始的任务失败
        INPUT: reason - 关闭原因
        OUTPUT: None
        SIDE EFFECT: 设置关闭标志
        FAILURE: 无 (幂等操作)
        """
        self._runtime.begin_shutdown(reason=reason)

    def close(self) -> None:
        """
        关闭任务管理器

        INTENT: 请求后台关闭
        INPUT: None
        OUTPUT: None
        SIDE EFFECT: 停止后台线程
        FAILURE: 无
        """
        self._runtime.close()

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def _build_submission_error(self, exc: ValueError) -> TaskSubmissionError:
        if self._runtime.is_shutting_down():
            return TaskSubmissionError(TaskErrorCode.SHUTDOWN, str(exc))
        return TaskSubmissionError(TaskErrorCode.QUEUE_FULL, str(exc))
