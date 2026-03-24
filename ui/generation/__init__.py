"""
ui/generation - 图像生成 UI 模块

INTENT:
    提供图像生成功能的 UI 组件、事件处理和状态管理。
    这是 ui/generation feature slice 的公开入口。

PUBLIC API:
    - entry.py: 模块主入口函数
    - contracts.py: 公开类型契约
    - OutputPresenter, OutputViewModel: 展示器（跨 feature 共享）

INTERNAL:
    - _internal/: 私有实现，禁止跨 feature 导入
"""

from ui.generation.contracts import (
    GenerationUIState,
    GenerationUIConfig,
)
from ui.generation._internal.presenter import OutputPresenter
from ui.generation._internal.view_model import OutputViewModel

__all__ = [
    # Contracts
    "GenerationUIState",
    "GenerationUIConfig",
    # Presenter (public - shared across features)
    "OutputViewModel",
    "OutputPresenter",
]
