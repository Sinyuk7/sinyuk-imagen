"""
core/tasking - 任务管理核心业务模块

INTENT:
    提供任务调度和管理的核心业务逻辑。
    这是 tasking feature slice 的公开入口。

PUBLIC API:
    - TaskManager: 任务管理器
    - TaskSubmissionError: 任务提交错误

INTERNAL:
    - _internal/: 私有实现，禁止跨 feature 导入
"""

from core.tasking.contracts import (
    TaskMetrics,
    TaskResult,
    TaskSubmission,
)
from core.tasking.entry import (
    TaskManager,
    TaskSubmissionError,
)

__all__ = [
    # 契约类型
    "TaskMetrics",
    "TaskResult",
    "TaskSubmission",
    # 服务类
    "TaskManager",
    # 异常
    "TaskSubmissionError",
]