"""
ui/dashboard/_internal/handler - Task Dashboard 事件处理器

INTENT:
    提供任务仪表盘的刷新、选择和错误处理逻辑。

SIDE EFFECT: 
    - 查询 core API 获取任务列表
    - 更新 UI 状态
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import gradio as gr # pyright: ignore[reportMissingImports]

import core.api as core_api
from core.schemas import BrowserTaskState, BrowserTaskStateValue, TaskErrorCode
from ui.dashboard.contracts import DashboardResponse
from ui.generation import OutputPresenter
from ui.dashboard._internal.presenter import TaskDashboardPresenter
from ui.state_machine import StateMachine

if TYPE_CHECKING:
    pass


class TaskDashboardHandler:
    """Refresh and selection handlers for task dashboard UI.
    
    INTENT: 处理任务列表刷新和选择事件
    INPUT: browser_state, state_machine
    OUTPUT: Dashboard 更新元组
    SIDE EFFECT: 调用 core API
    FAILURE: 返回空/默认状态
    """

    def hydrate_dashboard(
        self,
        browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
        state_machine: "StateMachine",
    ) -> DashboardResponse:
        browser_state = BrowserTaskState.from_value(browser_state_value)
        return self._build_dashboard_response(
            browser_state=browser_state,
            state_machine=state_machine,
        )

    def refresh_dashboard(
        self,
        browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
        state_machine: "StateMachine",
    ) -> DashboardResponse:
        browser_state = BrowserTaskState.from_value(browser_state_value)
        return self._build_dashboard_response(
            browser_state=browser_state,
            state_machine=state_machine,
        )

    def select_task(
        self,
        selected_task_id: str | None,
        browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
        state_machine: "StateMachine",
    ) -> DashboardResponse:
        browser_state = BrowserTaskState.from_value(browser_state_value)
        browser_state = BrowserTaskState(
            task_ids=list(browser_state.task_ids),
            selected_task_id=selected_task_id or browser_state.selected_task_id,
        )
        return self._build_dashboard_response(
            browser_state=browser_state,
            state_machine=state_machine,
        )

    def build_submission_error_response(
        self,
        *,
        browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
        state_machine: "StateMachine",
        error_code: TaskErrorCode | None,
        error_message: str,
    ) -> DashboardResponse:
        browser_state = BrowserTaskState.from_value(browser_state_value)
        response = self._build_dashboard_response(
            browser_state=browser_state,
            state_machine=state_machine,
        )
        error_view_model = OutputPresenter.build_error_result(
            error_message=error_message,
            error_code=error_code,
        )
        self.sync_slider_temp_files(
            state_machine,
            temp_paths=error_view_model.slider_temp_paths,
        )
        return DashboardResponse(
            browser_state_value=response.browser_state_value,
            selected_task_markdown=response.selected_task_markdown,
            gallery_items=error_view_model.gallery_items,
            status_text=error_view_model.status_text,
            logcat_markdown=error_view_model.logcat_markdown,
            slider_value=error_view_model.slider_value,
            task_selector_update=response.task_selector_update,
            refresh_interval_seconds=response.refresh_interval_seconds,
            admin_metrics_markdown=response.admin_metrics_markdown,
            state_machine=response.state_machine,
        )

    def sync_slider_temp_files(
        self,
        state_machine: "StateMachine",
        temp_paths: list[str],
    ) -> None:
        """Sync slider temp file paths to the state machine context."""
        state_machine.context.replace_slider_temp_paths(temp_paths)

    def _build_dashboard_response(
        self,
        *,
        browser_state: BrowserTaskState,
        state_machine: "StateMachine",
    ) -> DashboardResponse:
        snapshots = core_api.list_tasks(browser_state.task_ids)
        metrics_snapshot = core_api.get_task_metrics()
        view_model = TaskDashboardPresenter.build(
            browser_state=browser_state,
            snapshots=snapshots,
            metrics_snapshot=metrics_snapshot,
        )
        self.sync_slider_temp_files(
            state_machine,
            temp_paths=view_model.detail_view_model.slider_temp_paths,
        )
        task_selector_update = gr.update(
            choices=view_model.task_choices,
            value=view_model.selected_task_id,
        )
        return DashboardResponse(
            browser_state_value=view_model.browser_state.to_value(),
            selected_task_markdown=view_model.selected_task_markdown,
            gallery_items=view_model.detail_view_model.gallery_items,
            status_text=view_model.detail_view_model.status_text,
            logcat_markdown=view_model.detail_view_model.logcat_markdown,
            slider_value=view_model.detail_view_model.slider_value,
            task_selector_update=task_selector_update,
            refresh_interval_seconds=view_model.refresh_interval_seconds,
            admin_metrics_markdown=view_model.admin_metrics_markdown,
            state_machine=state_machine,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = ["TaskDashboardHandler"]
