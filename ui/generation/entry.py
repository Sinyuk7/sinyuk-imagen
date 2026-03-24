"""
ui/generation/entry - 图像生成 UI 模块入口

INTENT:
    提供图像生成 UI 功能的公开入口函数。
    这些函数是外部调用 ui/generation 模块的唯一合法路径。

SIDE EFFECT: UI 状态管理
"""

from ui.generation.contracts import GenerationUIComponents, GenerationUIConfig, GenerationUIState
from ui.generation._internal.advanced_params import AdvancedParamsPanel
from ui.generation._internal.basic_params import BasicParamsPanel
from ui.generation._internal.controls import ControlsPanel
from ui.generation._internal.handlers import (
    FlipRatioHandler,
    GenerateHandler,
    ProviderHandler,
)
from ui.generation._internal.output import OutputPanel


def build_generation_ui(config: GenerationUIConfig) -> GenerationUIComponents:
    """
    构建图像生成 UI

    INTENT: 创建图像生成功能的完整 UI 组件树
    INPUT: GenerationUIConfig - UI 配置
    OUTPUT: GenerationUIComponents - generation slice 的面板实例集合
    SIDE EFFECT: None (纯 UI 构建)
    FAILURE: 抛出 ValueError (配置无效)
    """
    if config.ui_context is None:
        raise ValueError("GenerationUIConfig.ui_context is required")
    if config.dashboard_handler is None:
        raise ValueError("GenerationUIConfig.dashboard_handler is required")

    basic_params = BasicParamsPanel(config.ui_context)
    advanced_params = AdvancedParamsPanel()
    controls = ControlsPanel()
    output = OutputPanel(show_admin_tab=config.show_admin_tab)
    provider_handler = ProviderHandler(config.ui_context)
    generate_handler = GenerateHandler(config.dashboard_handler)
    flip_ratio_handler = FlipRatioHandler(config.ui_context)

    return GenerationUIComponents(
        basic_params=basic_params,
        advanced_params=advanced_params,
        controls=controls,
        output=output,
        provider_handler=provider_handler,
        generate_handler=generate_handler,
        flip_ratio_handler=flip_ratio_handler,
    )


def bind_generation_events(
    ui_components: GenerationUIComponents,
    state: GenerationUIState,
) -> None:
    """
    绑定图像生成 UI 事件

    INTENT: 将 UI 组件的事件绑定到相应的处理函数
    INPUT:
        - ui_components: build_generation_ui 返回的组件集合
        - state: 初始 UI 状态
    OUTPUT: None
    SIDE EFFECT: 注册事件回调
    FAILURE: 抛出 ValueError (组件不兼容)
    """
    # 事件绑定逻辑由 ui/app.py 统一管理，此函数保留 feature slice 入口形式
    _ = (ui_components, state)
