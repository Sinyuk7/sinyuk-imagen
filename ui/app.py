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
    build_page_session_id_state,
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
        self.page_session_id_state: gr.State | None = None
        self.session_state_machine: gr.State | None = None
        self.session_warning_banner: gr.Markdown | None = None
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
            self.page_session_id_state = build_page_session_id_state()
            self.session_state_machine = gr.State(
                value=build_session_state(self.ui_context, self.generation_ui)
            )
            self.browser_task_state = build_browser_task_state_block()
            self.refresh_timer = build_refresh_timer_block()
            gr.Markdown(f"# {title}")
            self.session_warning_banner = gr.Markdown(
                value="",
                visible=False,
                elem_id="session-warning-banner",
            )

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
                fn=lambda browser_state_value, page_session_id_value, state_machine: hydrate_dashboard_outputs(
                    self.dashboard_ui,
                    browser_state_value,
                    page_session_id_value,
                    state_machine,
                ),
                inputs=[browser_task_state, self._require_page_session_id_state(), session_state_machine],
                outputs=[
                    browser_task_state,
                    self._require_page_session_id_state(),
                    self._require_session_warning_banner(),
                    output.get_gallery(),
                    output.get_status_bar(),
                    output.get_logcat_output(),
                    output.get_image_slider(),
                    output.get_mark_saved_button(),
                    output.get_mark_all_saved_button(),
                    output.get_task_history_list(),
                    output.get_task_selection_bridge(),
                    refresh_timer,
                    output.get_admin_metrics(),
                    session_state_machine,
                ],
                queue=False,
            )
            app.load(
                fn=None,
                js=_build_app_load_js(),
                inputs=None,
                outputs=None,
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

    def _require_page_session_id_state(self) -> gr.State:
        """Return the initialized page-session id state holder."""
        assert self.page_session_id_state is not None
        return self.page_session_id_state

    def _require_browser_task_state_block(self) -> Block:
        """Return the initialized browser task state block."""
        assert self.browser_task_state is not None
        return self.browser_task_state

    def _require_session_warning_banner(self) -> gr.Markdown:
        """Return the initialized session warning banner."""
        assert self.session_warning_banner is not None
        return self.session_warning_banner

    def _require_refresh_timer_block(self) -> Block:
        """Return the initialized refresh timer block."""
        assert self.refresh_timer is not None
        return self.refresh_timer

    def _bind_events(self) -> None:
        """Bind UI component events to handlers."""
        bind_generation_events(
            self.generation_ui,
            self._require_prepared_reference_state(),
            self._require_session_warning_banner(),
            self._require_browser_task_state_block(),
            self._require_page_session_id_state(),
            self._require_session_state_machine(),
            self._require_refresh_timer_block(),
        )
        bind_dashboard_events(
            self.dashboard_ui,
            self.generation_ui,
            self._require_session_warning_banner(),
            self._require_browser_task_state_block(),
            self._require_page_session_id_state(),
            self._require_session_state_machine(),
            self._require_refresh_timer_block(),
        )


def build_app(ui_context: UIContext | None = None) -> gr.Blocks:
    """Build and return the configured Gradio application."""
    if ui_context is None:
        ui_context = core_api.get_ui_context()
    app = Application(ui_context)
    return app.build()


def _build_app_load_js() -> str:
    """Return JS that wires unload warnings and custom task-row selection."""
    return """
() => {
  const bannerSelector = '#session-warning-banner';
  const taskListSelector = '#task-history-list';
  const taskSelectionBridgeSelector = '#task-selection-bridge';
  const hasUnsavedOutputs = () => {
    const banner = document.querySelector(bannerSelector);
    if (!banner) return false;
    const style = window.getComputedStyle(banner);
    const text = (banner.textContent || '').trim();
    return style.display !== 'none' && style.visibility !== 'hidden' && text.length > 0;
  };
  const getSelectionBridge = () =>
    document.querySelector(`${taskSelectionBridgeSelector} textarea, ${taskSelectionBridgeSelector} input`);
  const setBridgeValue = (nextValue) => {
    const bridge = getSelectionBridge();
    if (!bridge) return;
    const prototype = bridge.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
    if (descriptor && descriptor.set) {
      descriptor.set.call(bridge, nextValue);
    } else {
      bridge.value = nextValue;
    }
    bridge.dispatchEvent(new Event('input', { bubbles: true }));
    bridge.dispatchEvent(new Event('change', { bubbles: true }));
  };

  if (window.__sinyukBeforeUnloadHandler) {
    window.removeEventListener('beforeunload', window.__sinyukBeforeUnloadHandler);
  }
  if (window.__sinyukTaskRowClickHandler) {
    document.removeEventListener('click', window.__sinyukTaskRowClickHandler);
  }

  window.__sinyukBeforeUnloadHandler = (event) => {
    if (!hasUnsavedOutputs()) return;
    event.preventDefault();
    event.returnValue = '';
  };
  window.__sinyukTaskRowClickHandler = (event) => {
    const taskList = document.querySelector(taskListSelector);
    if (!taskList) return;
    const row = event.target.closest('[data-task-id]');
    if (!row || !taskList.contains(row)) return;
    const taskId = row.getAttribute('data-task-id');
    if (!taskId) return;
    setBridgeValue(taskId);
  };

  window.addEventListener('beforeunload', window.__sinyukBeforeUnloadHandler);
  document.addEventListener('click', window.__sinyukTaskRowClickHandler);
}
"""
