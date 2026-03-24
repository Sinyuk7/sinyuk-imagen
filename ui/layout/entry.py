"""
ui/layout/entry - 应用布局 UI 模块入口

INTENT:
    提供应用布局 UI 功能的公开入口函数。
    这些函数是外部调用 ui/layout 模块的唯一合法路径。

SIDE EFFECT: None (纯 UI 构建)
"""

from ui.layout.contracts import FooterConfig, LayoutComponents, LayoutConfig
from ui.layout._internal.footer import FooterPanel


def build_app_layout(config: LayoutConfig) -> LayoutComponents:
    """
    构建应用整体布局

    INTENT: 创建 layout slice 暴露给应用层的布局对象
    INPUT: LayoutConfig - 布局配置
    OUTPUT: LayoutComponents - 布局入口对象集合
    SIDE EFFECT: None (纯 UI 构建)
    FAILURE: 抛出 ValueError (配置无效)
    """
    return LayoutComponents(footer=build_footer(config.footer))


def build_footer(config: FooterConfig) -> FooterPanel:
    """
    构建页脚组件

    INTENT: 创建应用页脚 UI
    INPUT: FooterConfig - 页脚配置
    OUTPUT: FooterPanel - 页脚面板对象
    SIDE EFFECT: None (纯 UI 构建)
    FAILURE: 抛出 ValueError (配置无效)
    """
    _ = config
    return FooterPanel()
