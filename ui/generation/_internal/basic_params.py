"""Basic parameter panel for the generation slice."""

from __future__ import annotations

import gradio as gr

from core.schemas import ProviderUIContext, UIContext
from ui.generation._internal.component_base import BaseComponent

DEFAULT_PROMPT_PLACEHOLDER = "Describe the image you want to generate..."


class BasicParamsPanel(BaseComponent):
    """Render and manage the basic generation controls."""

    def __init__(self, ui_context: UIContext):
        super().__init__("basic_params")
        self.ui_context = ui_context
        self._providers = list(ui_context.providers.values())
        if not self._providers:
            raise ValueError("UI context must provide at least one provider")
        self._provider_map = {
            provider.provider_id: provider for provider in self._providers
        }
        self._initial_provider = self._resolve_initial_provider()
        self._initial_provider_context = self._provider_map[self._initial_provider]

    def render(self) -> None:
        """Render the basic parameter panel."""
        self._components["prompt"] = gr.Textbox(
            label="Prompt",
            placeholder=self._initial_provider_context.prompt_hint
            or DEFAULT_PROMPT_PLACEHOLDER,
            lines=4,
        )

        with gr.Row():
            self._components["provider"] = gr.Dropdown(
                choices=[provider.provider_id for provider in self._providers],
                value=self._initial_provider,
                label="Provider",
            )
            self._components["model"] = gr.Dropdown(
                choices=list(self._initial_provider_context.models),
                value=self._resolve_initial_model(),
                label="Model",
            )

        with gr.Row(equal_height=True):
            with gr.Column(scale=2):
                self._components["reference_image"] = gr.Image(
                    label="📷 Image",
                    type="filepath",
                    sources=["upload", "clipboard"],
                    height=180,
                    buttons=[],
                )
                self._components["ref_image_info"] = gr.Markdown("", visible=False)

            with gr.Column(scale=1):
                self._components["divisible_by"] = gr.Dropdown(
                    choices=[1, 8, 16, 32, 64],
                    value=16,
                    label="Divisible By",
                    info="Align dimensions to N×",
                )
                self._components["aspect_ratio"] = gr.Dropdown(
                    choices=["original"]
                    + list(self._initial_provider_context.aspect_ratios),
                    value=(
                        self._initial_provider_context.aspect_ratios[0]
                        if self._initial_provider_context.aspect_ratios
                        else "1:1"
                    ),
                    label="Aspect Ratio",
                )
                self._components["flip_ratio"] = gr.Checkbox(
                    label="Swap Width/Height",
                    value=False,
                )

        with gr.Row():
            self._components["batch_count"] = gr.Slider(
                minimum=1,
                maximum=self._initial_provider_context.max_images,
                value=1,
                step=1,
                label="Batch Count",
                visible=(self._initial_provider_context.max_images > 1),
                scale=1,
            )
            self._components["resolution"] = gr.Dropdown(
                choices=list(self._initial_provider_context.resolutions),
                value=(
                    self._initial_provider_context.resolutions[0]
                    if self._initial_provider_context.resolutions
                    else "2K"
                ),
                label="Resolution",
                scale=1,
            )

    def get_provider_context(self, provider_id: str) -> ProviderUIContext:
        """Return the provider context for the given provider id."""
        if provider_id not in self._provider_map:
            raise ValueError(f"Unknown provider '{provider_id}' in UI context")
        return self._provider_map[provider_id]

    def _resolve_initial_provider(self) -> str:
        if self.ui_context.active_provider in self._provider_map:
            return self.ui_context.active_provider
        return self._providers[0].provider_id

    def _resolve_initial_model(self) -> str | None:
        context = self._initial_provider_context
        if context.default_model in context.models:
            return context.default_model
        return context.models[0] if context.models else None

    @staticmethod
    def validate_image_dimensions(
        image_path: str | None,
        divisible_by: int,
    ) -> gr.Markdown:
        """Validate image dimensions and surface a small UI hint."""
        if image_path is None:
            return gr.Markdown(value="", visible=False)

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size

            info_text = f"📐 **{width} × {height}**"
            if divisible_by > 1 and (
                width % divisible_by != 0 or height % divisible_by != 0
            ):
                gr.Warning(
                    f"⚠️ 图片尺寸 ({width}×{height}) 不能被 {divisible_by} 整除，将被裁剪。"
                )
            return gr.Markdown(value=info_text, visible=True)
        except Exception:
            return gr.Markdown(value="", visible=False)
