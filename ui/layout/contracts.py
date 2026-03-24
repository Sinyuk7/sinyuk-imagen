"""
ui/layout/contracts - 应用布局 UI 模块的公开类型契约

INTENT:
    定义 ui/layout 模块与外部交互的所有类型契约。
    这些类型是稳定的公开 API，修改需要考虑向后兼容。

SIDE EFFECT: None (纯类型定义)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.layout._internal.footer import FooterPanel


@dataclass(frozen=True)
class FooterConfig:
    """
    页脚配置

    INTENT: 描述页脚 UI 的配置参数
    INPUT: 由 Application 层传入
    """
    show_version: bool = True
    show_links: bool = True
    version_text: str = ""
    custom_html: str | None = None


@dataclass(frozen=True)
class LayoutConfig:
    """
    应用布局配置

    INTENT: 描述应用整体布局的配置参数
    INPUT: 由 Application 层传入
    """
    title: str = "Imagen"
    theme: str = "default"
    enable_dark_mode: bool = True
    footer: FooterConfig = FooterConfig()
    max_width: str | None = None


@dataclass(frozen=True)
class LayoutComponents:
    """
    布局入口组件集合

    INTENT: 聚合 layout slice 暴露给应用层的布局对象
    """

    footer: "FooterPanel"
