"""Dashboard-specific orchestration helpers for the top-level app shell."""

from __future__ import annotations

import gradio as gr
from gradio.blocks import Block

from core.schemas import BrowserTaskState, BrowserTaskStateValue
from ui.dashboard.contracts import DashboardUIComponents
from ui.generation.contracts import GenerationUIComponents
from ui.state_machine import StateMachine


def hydrate_dashboard_outputs(
    dashboard_ui: DashboardUIComponents,
    browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
    state_machine: StateMachine,
) -> tuple[object, ...]:
    """Convert dashboard hydration into the raw Gradio output tuple."""
    response = dashboard_ui.handler.hydrate_dashboard(browser_state_value, state_machine)
    return response.to_output_tuple()


def refresh_dashboard_outputs(
    dashboard_ui: DashboardUIComponents,
    browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
    state_machine: StateMachine,
) -> tuple[object, ...]:
    """Convert dashboard refresh into the raw Gradio output tuple."""
    response = dashboard_ui.handler.refresh_dashboard(browser_state_value, state_machine)
    return response.to_output_tuple()


def select_task_outputs(
    dashboard_ui: DashboardUIComponents,
    selected_task_id: str | None,
    browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
    state_machine: StateMachine,
) -> tuple[object, ...]:
    """Convert task selection into the raw Gradio output tuple."""
    response = dashboard_ui.handler.select_task(
        selected_task_id,
        browser_state_value,
        state_machine,
    )
    return response.to_output_tuple()


def bind_dashboard_events(
    dashboard_ui: DashboardUIComponents,
    generation_ui: GenerationUIComponents,
    browser_task_state: Block,
    session_state_machine: gr.State,
    refresh_timer: Block,
) -> None:
    """Bind dashboard task selection and auto-refresh callbacks."""
    output = generation_ui.output

    output.get_task_selector().change(
        fn=lambda selected_task_id, browser_state_value, state_machine: select_task_outputs(
            dashboard_ui,
            selected_task_id,
            browser_state_value,
            state_machine,
        ),
        inputs=[
            output.get_task_selector(),
            browser_task_state,
            session_state_machine,
        ],
        outputs=[
            browser_task_state,
            output.get_current_task(),
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

    if hasattr(refresh_timer, "tick"):
        refresh_timer.tick(
            fn=lambda browser_state_value, state_machine: refresh_dashboard_outputs(
                dashboard_ui,
                browser_state_value,
                state_machine,
            ),
            inputs=[browser_task_state, session_state_machine],
            outputs=[
                browser_task_state,
                output.get_current_task(),
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
