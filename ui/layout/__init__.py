"""
ui/layout - 布局 UI 模块

INTENT:
    提供页面布局组件（如 header、footer、sidebar）。
    这是 ui/layout feature slice 的公开入口。

PUBLIC API:
    - _internal/footer.py: Footer 组件 (FooterPanel)

INTERNAL:
    - _internal/: 私有实现，禁止跨 feature 导入
"""

from ui.layout._internal.footer import FooterPanel

__all__ = [
    "FooterPanel",
]