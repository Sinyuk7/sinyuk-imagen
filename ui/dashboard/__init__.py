"""
ui/dashboard - 任务仪表盘 UI 模块

INTENT:
    提供任务列表和任务详情展示的 UI 组件和状态管理。
    这是 ui/dashboard feature slice 的公开入口。

PUBLIC API:
    - entry.py: 模块主入口函数
    - contracts.py: 公开类型契约
    - TaskDashboardHandler, TaskDashboardPresenter, TaskDashboardViewModel: 公开 API

INTERNAL:
    - _internal/: 私有实现，禁止跨 feature 导入
"""

from ui.dashboard._internal.handler import TaskDashboardHandler
from ui.dashboard._internal.presenter import (
    TaskDashboardViewModel,
    TaskDashboardPresenter,
)

__all__ = [
    "TaskDashboardHandler",
    "TaskDashboardViewModel",
    "TaskDashboardPresenter",
]