"""
ui/generation/_internal/handlers - Generation UI 事件处理器

INTENT:
    提供图像生成 UI 的事件处理逻辑。

SIDE EFFECT: 
    - 调用 core API 提交任务
    - 更新 UI 状态
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, cast

import gradio as gr # pyright: ignore[reportMissingImports]

import core.api as core_api
from core.schemas import (
    BrowserTaskState,
    BrowserTaskStateValue,
    ProviderUIContext,
    TaskConfig,
    TaskErrorCode,
    UIContext,
)
from ui._app_state import ensure_page_session_id
from ui.dashboard.contracts import DashboardResponse
from ui.generation.contracts import (
    DashboardHandlerPort,
    FlipRatioResponse,
    GenerationResponse,
    ProviderExtraParams,
)
from ui.events import Event, EventType
from ui.state_machine import StateMachine

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

DEFAULT_PROMPT_PLACEHOLDER = "Describe the image you want to generate..."


# =============================================================================
# Flip Ratio Utilities
# =============================================================================


def flip_ratio_value(ratio: str) -> str:
    """翻转单个 ratio 值，如 '2:3' → '3:2'。

    INTENT: 将宽高比字符串中的宽高互换
    INPUT: ratio - 宽高比字符串，如 '2:3' 或 'original'
    OUTPUT: 翻转后的字符串，如 '3:2'；'original' 保持不变
    SIDE EFFECT: None
    FAILURE: 格式不符时返回原值
    """
    if ":" not in ratio or ratio == "original":
        return ratio
    parts = ratio.split(":")
    if len(parts) != 2:
        return ratio
    return f"{parts[1]}:{parts[0]}"


def flip_ratio_choices(choices: list[str], should_flip: bool) -> list[str]:
    """根据 should_flip 标志翻转整个 choices 列表。

    INTENT: 批量翻转下拉菜单的所有选项
    INPUT: choices - 选项列表, should_flip - 是否翻转
    OUTPUT: 翻转后的选项列表（或原列表）
    SIDE EFFECT: None
    FAILURE: None
    """
    if not should_flip:
        return choices
    return [flip_ratio_value(c) for c in choices]


# =============================================================================
# Generate Handler
# =============================================================================


class GenerateHandler:
    """Handle task submission and map inputs to TaskConfig.
    
    INTENT: 处理生成按钮点击事件，构建 TaskConfig 并提交到 core API
    INPUT: UI 表单参数
    OUTPUT: Dashboard 更新响应
    SIDE EFFECT: DB_WRITE (任务记录), NETWORK (provider 调用)
    FAILURE: 返回错误响应而非抛出异常
    """

    def __init__(self, dashboard_handler: DashboardHandlerPort):
        self.dashboard_handler = dashboard_handler

    def handle_generate(
        self,
        prompt_text: str,
        provider_name: str,
        model_name: str,
        img_count: int,
        ratio: str,
        flip_checked: bool,
        resolution: str,
        neg_prompt: str | None,
        seed_val: float | None,
        guidance_enabled: bool,
        guidance_val: float,
        advanced_json: str,
        provider_token_val: str,
        debug_mode: bool,
        reference_image_path: str | None,
        divisible_by: int,
        browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
        page_session_id_value: str | None | object,
        state_machine: "StateMachine",
    ) -> DashboardResponse:
        """
        INTENT: 处理图像生成请求
        INPUT: UI 表单中的所有参数
        OUTPUT: Dashboard 更新元组
        SIDE EFFECT: DB_WRITE | NETWORK
        FAILURE: 返回错误响应
        """
        browser_state = BrowserTaskState.from_value(browser_state_value)
        page_session_id = ensure_page_session_id(page_session_id_value)
        state_machine.context.set_token(provider_name, provider_token_val or "")

        try:
            extra = self._parse_advanced_json(advanced_json)
            task_config = self._build_task_config(
                prompt_text=prompt_text,
                provider_name=provider_name,
                model_name=model_name,
                img_count=img_count,
                ratio=ratio,
                flip_checked=flip_checked,
                resolution=resolution,
                neg_prompt=neg_prompt,
                seed_val=seed_val,
                guidance_enabled=guidance_enabled,
                guidance_val=guidance_val,
                extra=extra,
                provider_token_val=provider_token_val,
                debug_mode=debug_mode,
                reference_image_path=reference_image_path,
                divisible_by=divisible_by,
            )

            logger.info(
                "Generate request: provider=%s, model=%s, prompt='%s...', debug_mode=%s",
                provider_name,
                model_name,
                prompt_text[:50],
                debug_mode,
            )
            task_id = core_api.submit_generation_task(
                task_config,
                owner_session_id=page_session_id,
            )
            next_browser_state = browser_state.with_task(task_id)
            return self.dashboard_handler.hydrate_dashboard(
                next_browser_state.to_value(),
                page_session_id,
                state_machine,
            )

        except Exception as exc:
            error_code = getattr(exc, "code", None)
            if error_code is None and isinstance(exc, ValueError):
                error_code = TaskErrorCode.INVALID_REQUEST
            if error_code is None:
                logger.exception("Generate handler error: %s", exc)
                error_code = TaskErrorCode.INVALID_REQUEST

            return self.dashboard_handler.build_submission_error_response(
                browser_state_value=browser_state.to_value(),
                page_session_id_value=page_session_id,
                state_machine=state_machine,
                error_code=error_code,
                error_message=str(exc),
            )

    def _parse_advanced_json(self, advanced_json: str) -> ProviderExtraParams:
        if not advanced_json or not advanced_json.strip():
            return {}

        try:
            parsed = json.loads(advanced_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in advanced parameters: {exc}") from exc

        if not isinstance(parsed, dict):
            raise ValueError("Advanced parameters must be a JSON object (dict)")

        return cast(ProviderExtraParams, parsed)

    def _build_task_config(
        self,
        *,
        prompt_text: str,
        provider_name: str,
        model_name: str,
        img_count: int,
        ratio: str,
        flip_checked: bool,
        resolution: str,
        neg_prompt: str | None,
        seed_val: float | None,
        guidance_enabled: bool,
        guidance_val: float,
        extra: ProviderExtraParams,
        provider_token_val: str,
        debug_mode: bool,
        reference_image_path: str | None,
        divisible_by: int,
    ) -> TaskConfig:
        # ratio is already flipped by UI when flip_checked is True,
        # so we use it directly. flip_checked param kept for API compatibility.
        _ = flip_checked  # Unused now - ratio already reflects flip state
        final_ratio = ratio

        return TaskConfig(
            prompt=prompt_text,
            provider=provider_name,
            model=model_name,
            params={
                "image_count": img_count,
                "aspect_ratio": final_ratio,
                "resolution": resolution,
                "seed": seed_val,
                "negative_prompt": neg_prompt,
                "guidance_scale": guidance_val if guidance_enabled else None,
            },
            extra=extra,
            ui_token_override=provider_token_val,
            debug_mode=bool(debug_mode),
            reference_image_path=reference_image_path,
            divisible_by=divisible_by,
        )


# =============================================================================
# Provider Handler
# =============================================================================


class ProviderHandler:
    """Provider 切换处理器。

    INTENT: 处理 Provider 切换时的级联更新逻辑
    INPUT: provider_name, 当前 token, state_machine
    OUTPUT: UI 更新对象元组
    SIDE EFFECT: 更新 state_machine context
    FAILURE: 抛出 ValueError (未知 provider)
    """

    def __init__(self, ui_context: UIContext):
        self.ui_context = ui_context
        self._providers = list(self.ui_context.providers.values())
        if not self._providers:
            raise ValueError("UI context must provide at least one provider")
        self._provider_map = {
            provider.provider_id: provider for provider in self._providers
        }

    def handle_provider_change(
        self,
        provider_name: str,
        current_token: str,
        flip_checked: bool,
        state_machine: "StateMachine",
    ) -> GenerationResponse:
        """处理 Provider 切换事件。"""
        provider = self._get_provider_context(provider_name)
        previous_provider = state_machine.context.current_provider
        if previous_provider:
            state_machine.context.set_token(previous_provider, current_token or "")

        state_machine.transition(
            Event(
                type=EventType.PROVIDER_CHANGED,
                payload={"provider": provider_name},
                source="provider_dropdown",
            )
        )
        state_machine.context.set_prompt_hint(provider_name, provider.prompt_hint or "")
        token_val = state_machine.context.get_token(provider_name)

        model_update = gr.update(
            choices=list(provider.models),
            value=self._resolve_default_model(provider),
        )

        batch_count_update = gr.update(
            visible=(provider.max_images > 1),
            maximum=provider.max_images,
            value=1,
        )

        base_choices = ["original"] + list(provider.aspect_ratios)
        base_value = provider.aspect_ratios[0] if provider.aspect_ratios else "1:1"
        aspect_ratio_update = gr.update(
            choices=flip_ratio_choices(base_choices, flip_checked),
            value=flip_ratio_value(base_value) if flip_checked else base_value,
        )

        resolution_update = gr.update(
            choices=list(provider.resolutions),
            value=provider.resolutions[0] if provider.resolutions else "2K",
        )

        token_update = gr.update(value=token_val)

        prompt_update = gr.update(
            placeholder=provider.prompt_hint or DEFAULT_PROMPT_PLACEHOLDER
        )

        state_machine.transition(
            Event(
                type=EventType.CONFIG_UPDATED,
                source="provider_handler",
            )
        )

        return GenerationResponse(
            model_update=model_update,
            batch_count_update=batch_count_update,
            aspect_ratio_update=aspect_ratio_update,
            resolution_update=resolution_update,
            token_update=token_update,
            prompt_update=prompt_update,
            state_machine=state_machine,
        )

    def save_token(
        self,
        provider_name: str,
        token: str,
        state_machine: "StateMachine",
    ) -> "StateMachine":
        """保存 Provider 的 token。"""
        state_machine.context.set_token(provider_name, token or "")
        return state_machine

    def _get_provider_context(self, provider_name: str) -> ProviderUIContext:
        if provider_name not in self._provider_map:
            raise ValueError(f"Unknown provider '{provider_name}' in UI context")
        return self._provider_map[provider_name]

    @staticmethod
    def _resolve_default_model(provider: ProviderUIContext) -> str | None:
        if provider.default_model in provider.models:
            return provider.default_model
        return provider.models[0] if provider.models else None


# =============================================================================
# Flip Ratio Handler
# =============================================================================


class FlipRatioHandler:
    """Flip Ratio 切换处理器。

    INTENT: 处理 flip_ratio checkbox 切换时更新 aspect_ratio 下拉菜单
    INPUT: flip_checked 状态, 当前 ratio, provider_name
    OUTPUT: FlipRatioResponse (aspect_ratio 下拉菜单更新)
    SIDE EFFECT: None
    FAILURE: 未知 provider 时抛出 ValueError
    """

    def __init__(self, ui_context: UIContext):
        self.ui_context = ui_context
        self._providers = list(self.ui_context.providers.values())
        if not self._providers:
            raise ValueError("UI context must provide at least one provider")
        self._provider_map = {
            provider.provider_id: provider for provider in self._providers
        }

    def handle_flip_change(
        self,
        flip_checked: bool,
        current_ratio: str,
        provider_name: str,
    ) -> FlipRatioResponse:
        """处理 flip_ratio checkbox 切换事件。

        INTENT: 根据 flip_checked 状态更新 aspect_ratio 下拉菜单的 choices 和 value
        INPUT: flip_checked - 是否选中, current_ratio - 当前选中值, provider_name - 当前 provider
        OUTPUT: FlipRatioResponse 包含 aspect_ratio 下拉菜单更新
        SIDE EFFECT: None
        FAILURE: 未知 provider 时抛出 ValueError
        """
        provider = self._get_provider_context(provider_name)
        base_choices = ["original"] + list(provider.aspect_ratios)
        new_choices = flip_ratio_choices(base_choices, flip_checked)
        new_value = flip_ratio_value(current_ratio)

        aspect_ratio_update = gr.update(
            choices=new_choices,
            value=new_value,
        )

        return FlipRatioResponse(aspect_ratio_update=aspect_ratio_update)

    def _get_provider_context(self, provider_name: str) -> ProviderUIContext:
        if provider_name not in self._provider_map:
            raise ValueError(f"Unknown provider '{provider_name}' in UI context")
        return self._provider_map[provider_name]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FlipRatioHandler",
    "GenerateHandler",
    "ProviderHandler",
]
