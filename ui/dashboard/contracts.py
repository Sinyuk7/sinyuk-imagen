"""
ui/dashboard/contracts - 任务仪表盘 UI 模块的公开类型契约

INTENT:
    定义 ui/dashboard 模块与外部交互的所有类型契约。
    这些类型是稳定的公开 API，修改需要考虑向后兼容。

SIDE EFFECT: None (纯类型定义)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from core.schemas import BrowserTaskStateValue
from core.schemas.ids import TaskId
from core.schemas.enums import TaskStatus
from ui.state_machine import StateMachine

if TYPE_CHECKING:
    from ui.dashboard._internal.handler import TaskDashboardHandler


@dataclass(frozen=True)
class DashboardUIConfig:
    """
    仪表盘 UI 配置

    INTENT: 描述仪表盘 UI 的初始化配置
    INPUT: 由 Application 层传入
    """
    max_visible_tasks: int = 20
    auto_refresh_interval_seconds: float = 2.0
    show_completed_tasks: bool = True
    show_failed_tasks: bool = True


@dataclass
class TaskDisplayItem:
    """
    任务展示项

    INTENT: 用于 UI 展示的单个任务信息
    """
    task_id: TaskId
    status: TaskStatus
    description: str
    created_at: datetime
    elapsed_seconds: float | None = None
    error_message: str | None = None

    @property
    def status_label(self) -> str:
        """状态展示文本"""
        return self.status.value.replace("_", " ").title()


@dataclass
class DashboardUIState:
    """
    仪表盘 UI 状态

    INTENT: 封装仪表盘 UI 当前的完整状态
    """
    tasks: list[TaskDisplayItem] = field(default_factory=list)
    total_count: int = 0
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    is_loading: bool = False
    last_refresh_at: datetime | None = None


@dataclass(frozen=True)
class DashboardResponse:
    """
    仪表盘多输出响应

    INTENT: 为 dashboard slice 的多输出更新提供具名类型
    """

    browser_state_value: BrowserTaskStateValue
    gallery_items: list[object]
    status_text: str
    logcat_markdown: str
    slider_value: object
    task_selector_update: object
    refresh_interval_seconds: float | None
    admin_metrics_markdown: str
    state_machine: "StateMachine"

    def to_output_tuple(
        self,
    ) -> tuple[
        BrowserTaskStateValue,
        list[object],
        str,
        str,
        object,
        object,
        float | None,
        str,
        "StateMachine",
    ]:
        return (
            self.browser_state_value,
            self.gallery_items,
            self.status_text,
            self.logcat_markdown,
            self.slider_value,
            self.task_selector_update,
            self.refresh_interval_seconds,
            self.admin_metrics_markdown,
            self.state_machine,
        )


@dataclass(frozen=True)
class DashboardUIComponents:
    """
    仪表盘入口组件集合

    INTENT: 聚合 dashboard slice 暴露给应用层的入口对象
    """

    handler: "TaskDashboardHandler"
