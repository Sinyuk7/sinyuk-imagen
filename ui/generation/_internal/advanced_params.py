"""Advanced parameter panel for the generation slice."""

from __future__ import annotations

import gradio as gr

from ui.generation._internal.component_base import BaseComponent


class AdvancedParamsPanel(BaseComponent):
    """Render advanced generation controls."""

    def __init__(self) -> None:
        super().__init__("advanced_params")

    def render(self) -> None:
        """Render the advanced parameter controls."""
        self._components["provider_token"] = gr.Textbox(
            label="Provider Token (Override)",
            placeholder="Optional. Overrides config/env token for the selected provider.",
            type="password",
        )

        with gr.Accordion("Advanced Settings", open=False):
            self._components["debug_mode"] = gr.Checkbox(
                label="Debug Mode (Dry Run)",
                value=False,
                info="When enabled, no real request is sent. A sanitized final request snapshot will be shown below.",
            )
            self._components["negative_prompt"] = gr.Textbox(
                label="Negative Prompt",
                placeholder="Describe what you don't want, e.g. blurry, low quality, bad anatomy...",
                lines=2,
            )
            with gr.Row():
                self._components["seed"] = gr.Number(
                    label="Seed",
                    precision=0,
                    value=None,
                    info="Random seed for reproducibility. Leave empty for random.",
                )
            with gr.Row():
                self._components["enable_guidance"] = gr.Checkbox(
                    label="启用 Guidance Scale",
                    value=False,
                    info="Enable to control prompt adherence strength.",
                )
                self._components["guidance_scale"] = gr.Slider(
                    label="Guidance Scale",
                    minimum=1.0,
                    maximum=20.0,
                    value=7.5,
                    step=0.1,
                    interactive=False,
                    info="Higher = stricter prompt adherence. Lower = more creative freedom.",
                )
            self._components["advanced_params"] = gr.Textbox(
                label="Extra Parameters (JSON)",
                placeholder='{"safety_filter_level": "BLOCK_NONE"}',
                lines=3,
                info="Provider-specific parameters as JSON. Goes into TaskConfig.extra.",
            )

    def setup_guidance_toggle(self) -> None:
        """Bind the guidance-enabled checkbox to the slider interactivity."""
        self._components["enable_guidance"].change(
            fn=lambda enabled: gr.update(interactive=enabled),
            inputs=[self._components["enable_guidance"]],
            outputs=[self._components["guidance_scale"]],
        )
