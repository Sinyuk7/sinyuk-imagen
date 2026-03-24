"""Gradio application builder."""

from __future__ import annotations

import gradio as gr # pyright: ignore[reportMissingImports]
from gradio.blocks import Block # pyright: ignore[reportMissingImports]

import core.api as core_api
from core.schemas import UIContext
from ui._app_dashboard import bind_dashboard_events, hydrate_dashboard_outputs
from ui._app_generation import bind_generation_events
from ui._app_state import (
    build_browser_task_state_block,
    build_prepared_reference_state,
    build_refresh_timer_block,
    build_session_state,
)
from ui.dashboard.contracts import DashboardUIConfig
from ui.dashboard.entry import build_dashboard_ui
from ui.generation.contracts import GenerationUIConfig
from ui.generation.entry import build_generation_ui
from ui.layout.contracts import FooterConfig, LayoutConfig
from ui.layout.entry import build_app_layout


class Application:
    """Compose the Gradio application from panels and handlers."""

    def __init__(self, ui_context: UIContext):
        self.ui_context = ui_context
        self.show_admin_tab = bool(ui_context.show_admin_tab)
        self.dashboard_ui = build_dashboard_ui(DashboardUIConfig())
        self.generation_ui = build_generation_ui(
            GenerationUIConfig(
                ui_context=self.ui_context,
                show_admin_tab=self.show_admin_tab,
                dashboard_handler=self.dashboard_ui.handler,
            )
        )
        self.layout_ui = build_app_layout(
            LayoutConfig(
                title=getattr(self.ui_context, "title", "Sinyuk Imagen"),
                footer=FooterConfig(),
            )
        )
        self.prepared_reference_image_path_state: gr.State | None = None
        self.session_state_machine: gr.State | None = None
        self.browser_task_state: Block | None = None
        self.refresh_timer: Block | None = None

    def build(self) -> gr.Blocks:
        """Build the Gradio Blocks application."""
        title = getattr(self.ui_context, "title", "Sinyuk Imagen")
        basic_params = self.generation_ui.basic_params
        advanced_params = self.generation_ui.advanced_params
        controls = self.generation_ui.controls
        output = self.generation_ui.output

        with gr.Blocks(title=title) as app:
            self.prepared_reference_image_path_state = build_prepared_reference_state()
            self.session_state_machine = gr.State(
                value=build_session_state(self.ui_context, self.generation_ui)
            )
            self.browser_task_state = build_browser_task_state_block()
            self.refresh_timer = build_refresh_timer_block()
            gr.Markdown(f"# {title}")

            with gr.Row():
                with gr.Column(scale=1):
                    basic_params.render()
                    advanced_params.render()
                    advanced_params.setup_guidance_toggle()
                    controls.render()

                with gr.Column(scale=1):
                    output.render()

            self.layout_ui.footer.render()
            self._bind_events()
            browser_task_state = self._require_browser_task_state_block()
            refresh_timer = self._require_refresh_timer_block()
            session_state_machine = self._require_session_state_machine()
            app.load(
                fn=lambda browser_state_value, state_machine: hydrate_dashboard_outputs(
                    self.dashboard_ui,
                    browser_state_value,
                    state_machine,
                ),
                inputs=[browser_task_state, session_state_machine],
                outputs=[
                    browser_task_state,
                    output.get_gallery(),
                    output.get_status_bar(),
                    output.get_logcat_output(),
                    output.get_image_slider(),
                    output.get_task_selector(),
                    refresh_timer,
                    output.get_admin_metrics(),
                    session_state_machine,
                ],
                queue=False,
            )

        return app

    def _require_session_state_machine(self) -> gr.State:
        """Return the initialized session state holder."""
        assert self.session_state_machine is not None
        return self.session_state_machine

    def _require_prepared_reference_state(self) -> gr.State:
        """Return the initialized prepared-reference state holder."""
        assert self.prepared_reference_image_path_state is not None
        return self.prepared_reference_image_path_state

    def _require_browser_task_state_block(self) -> Block:
        """Return the initialized browser task state block."""
        assert self.browser_task_state is not None
        return self.browser_task_state

    def _require_refresh_timer_block(self) -> Block:
        """Return the initialized refresh timer block."""
        assert self.refresh_timer is not None
        return self.refresh_timer

    def _bind_events(self) -> None:
        """Bind UI component events to handlers."""
        bind_generation_events(
            self.generation_ui,
            self._require_prepared_reference_state(),
            self._require_browser_task_state_block(),
            self._require_session_state_machine(),
            self._require_refresh_timer_block(),
        )
        bind_dashboard_events(
            self.dashboard_ui,
            self.generation_ui,
            self._require_browser_task_state_block(),
            self._require_session_state_machine(),
            self._require_refresh_timer_block(),
        )


def build_app(ui_context: UIContext | None = None) -> gr.Blocks:
    """Build and return the configured Gradio application."""
    if ui_context is None:
        ui_context = core_api.get_ui_context()
    app = Application(ui_context)
    return app.build()