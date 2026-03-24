"""
ui/generation/contracts - 图像生成 UI 模块的公开类型契约

INTENT:
    定义 ui/generation 模块与外部交互的所有类型契约。
    这些类型是稳定的公开 API，修改需要考虑向后兼容。

SIDE EFFECT: None (纯类型定义)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, TypeAlias

from core.schemas import BrowserTaskStateValue, TaskErrorCode

from core.schemas.ids import ProviderId, ModelId
from ui.state_machine import StateMachine

if TYPE_CHECKING:
    from core.schemas import UIContext
    from ui.dashboard.contracts import DashboardResponse
    from ui.generation._internal.advanced_params import (
        AdvancedParamsPanel,
    )
    from ui.generation._internal.basic_params import (
        BasicParamsPanel,
    )
    from ui.generation._internal.controls import (
        ControlsPanel,
    )
    from ui.generation._internal.handlers import GenerateHandler, ProviderHandler
    from ui.generation._internal.output import OutputPanel

ProviderExtraParams: TypeAlias = dict[str, object]
GalleryItemValue: TypeAlias = object
SliderValue: TypeAlias = object
GradioUpdateValue: TypeAlias = object


class DashboardHandlerPort(Protocol):
    """Small contract the generation slice needs from the dashboard slice."""

    def hydrate_dashboard(
        self,
        browser_state_value: BrowserTaskStateValue | object,
        state_machine: StateMachine,
    ) -> DashboardResponse: ...

    def build_submission_error_response(
        self,
        *,
        browser_state_value: BrowserTaskStateValue | object,
        state_machine: StateMachine,
        error_code: TaskErrorCode | None,
        error_message: str,
    ) -> DashboardResponse: ...


@dataclass(frozen=True)
class GenerationUIConfig:
    """
    图像生成 UI 配置

    INTENT: 描述 UI 的初始化配置
    INPUT: 由 Application 层传入
    """
    ui_context: "UIContext | None" = None
    available_providers: list[ProviderId] = field(default_factory=list)
    default_provider: ProviderId = ""
    default_model: ModelId = ""
    max_image_count: int = 4
    enable_reference_image: bool = True
    enable_advanced_params: bool = True
    show_admin_tab: bool = False
    dashboard_handler: DashboardHandlerPort | None = None


@dataclass
class GenerationUIState:
    """
    图像生成 UI 状态

    INTENT: 封装 UI 当前的完整状态
    """
    # 基础参数
    provider_id: ProviderId = ""
    model_id: ModelId = ""
    prompt: str = ""
    negative_prompt: str = ""
    image_count: int = 1

    # 高级参数
    aspect_ratio: str | None = None
    resolution: str | None = None
    reference_image_path: str | None = None

    # UI 状态
    is_generating: bool = False
    error_message: str | None = None

    # Provider 特定参数
    extra_params: ProviderExtraParams = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationUIComponents:
    """
    图像生成 UI 组件集合

    INTENT: 聚合 generation slice 暴露给应用层的面板实例
    """

    basic_params: "BasicParamsPanel"
    advanced_params: "AdvancedParamsPanel"
    controls: "ControlsPanel"
    output: "OutputPanel"
    provider_handler: "ProviderHandler"
    generate_handler: "GenerateHandler"


@dataclass(frozen=True)
class GenerationResponse:
    """
    Provider 切换后的 UI 响应

    INTENT: 为 generation slice 的多输出更新提供具名类型
    """

    model_update: GradioUpdateValue
    batch_count_update: GradioUpdateValue
    aspect_ratio_update: GradioUpdateValue
    resolution_update: GradioUpdateValue
    token_update: GradioUpdateValue
    prompt_update: GradioUpdateValue
    state_machine: "StateMachine"

    def to_output_tuple(
        self,
    ) -> tuple[
        GradioUpdateValue,
        GradioUpdateValue,
        GradioUpdateValue,
        GradioUpdateValue,
        GradioUpdateValue,
        GradioUpdateValue,
        "StateMachine",
    ]:
        return (
            self.model_update,
            self.batch_count_update,
            self.aspect_ratio_update,
            self.resolution_update,
            self.token_update,
            self.prompt_update,
            self.state_machine,
        )
