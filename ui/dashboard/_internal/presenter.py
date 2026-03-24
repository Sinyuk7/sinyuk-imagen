"""
ui/dashboard/_internal/presenter - Task Dashboard 展示器

INTENT:
    将任务快照列表转换为 UI 可渲染的仪表盘视图模型。

SIDE EFFECT: None (纯数据转换)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from core.schemas import (
    BrowserTaskState,
    TaskManagerMetricsSnapshot,
    TaskSnapshot,
    TaskStatus,
)

STATUS_EMOJI = {
    TaskStatus.QUEUED: "⏳",
    TaskStatus.PREPARING: "🔧",
    TaskStatus.RUNNING: "🔄",
    TaskStatus.SUCCEEDED: "✅",
    TaskStatus.FAILED: "❌",
    TaskStatus.TIMED_OUT: "⏱️",
}
from ui.generation import OutputPresenter, OutputViewModel

TaskChoice = Tuple[str, str]


@dataclass
class TaskDashboardViewModel:
    """UI-ready task dashboard state.
    
    INTENT: 表示任务仪表盘的完整视图状态
    """

    browser_state: BrowserTaskState = field(default_factory=BrowserTaskState)
    task_choices: List[TaskChoice] = field(default_factory=list)
    selected_task_id: Optional[str] = None
    detail_view_model: OutputViewModel = field(default_factory=OutputViewModel)
    refresh_interval_seconds: Optional[float] = None
    admin_metrics_markdown: str = ""


class TaskDashboardPresenter:
    """Map task snapshots into task list and detail view models.
    
    INTENT: 将任务快照列表转换为仪表盘视图模型
    INPUT: browser_state, snapshots, metrics_snapshot
    OUTPUT: TaskDashboardViewModel
    SIDE EFFECT: None
    FAILURE: 返回空/默认状态的 TaskDashboardViewModel
    """

    @staticmethod
    def build(
        *,
        browser_state: BrowserTaskState,
        snapshots: List[TaskSnapshot],
        metrics_snapshot: TaskManagerMetricsSnapshot,
    ) -> TaskDashboardViewModel:
        snapshot_map = {snapshot.task_id: snapshot for snapshot in snapshots}
        normalized_ids = [
            task_id for task_id in browser_state.task_ids if task_id in snapshot_map
        ]
        selected_task_id = browser_state.selected_task_id
        if selected_task_id not in snapshot_map:
            selected_task_id = normalized_ids[0] if normalized_ids else None

        selected_snapshot = (
            snapshot_map.get(selected_task_id) if selected_task_id else None
        )
        detail_view_model = TaskDashboardPresenter._build_detail_view_model(
            selected_snapshot
        )
        task_choices = [
            (
                TaskDashboardPresenter._build_task_choice_label(snapshot),
                snapshot.task_id,
            )
            for snapshot in snapshots
        ]
        refresh_interval = TaskDashboardPresenter._build_refresh_interval(snapshots)

        return TaskDashboardViewModel(
            browser_state=BrowserTaskState(
                task_ids=normalized_ids,
                selected_task_id=selected_task_id,
            ),
            task_choices=task_choices,
            selected_task_id=selected_task_id,
            detail_view_model=detail_view_model,
            refresh_interval_seconds=refresh_interval,
            admin_metrics_markdown=TaskDashboardPresenter._build_admin_metrics_markdown(
                metrics_snapshot
            ),
        )

    @staticmethod
    def _build_detail_view_model(snapshot: Optional[TaskSnapshot]) -> OutputViewModel:
        if snapshot is None:
            return OutputPresenter.build_empty_result()

        if snapshot.status == TaskStatus.SUCCEEDED and snapshot.result is not None:
            if snapshot.result.success and snapshot.result.images:
                return OutputPresenter.build_generation_success(snapshot.result)
            return OutputPresenter.build_error_result(
                error_message=snapshot.result.error or "Task failed.",
                error_code=snapshot.error_code,
                result=snapshot.result,
            )

        if snapshot.status == TaskStatus.FAILED:
            return OutputPresenter.build_error_result(
                error_message=snapshot.error or "Task failed.",
                error_code=snapshot.error_code,
                result=snapshot.result,
            )

        if snapshot.status == TaskStatus.TIMED_OUT:
            return OutputPresenter.build_error_result(
                error_message=snapshot.error or "Task timed out.",
                error_code=snapshot.error_code,
                result=snapshot.result,
            )

        return OutputPresenter.build_task_pending(snapshot)

    @staticmethod
    def _build_task_choice_label(snapshot: TaskSnapshot) -> str:
        """Build user-friendly task label with emoji status and relative time.
        
        Format:
            ✅ A beautiful sunset over the mountains...
               FLUX.1 · 3分钟前
        """
        emoji = STATUS_EMOJI.get(snapshot.status, "❓")
        prompt = snapshot.prompt_preview or "(empty prompt)"
        model = snapshot.model or "unknown"
        time_str = TaskDashboardPresenter._format_relative_time(snapshot.submitted_at)
        return f"{emoji} {prompt}\n   {model} · {time_str}"

    @staticmethod
    def _format_relative_time(dt: Optional[datetime]) -> str:
        """Convert timestamp to relative time (e.g., '3分钟前')."""
        if dt is None:
            return "未知"
        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "刚刚"
        elif seconds < 3600:
            return f"{seconds // 60}分钟前"
        elif seconds < 86400:
            return f"{seconds // 3600}小时前"
        else:
            return f"{seconds // 86400}天前"

    @staticmethod
    def _build_refresh_interval(snapshots: List[TaskSnapshot]) -> Optional[float]:
        if any(snapshot.status == TaskStatus.RUNNING for snapshot in snapshots):
            return 2.0
        if any(not snapshot.is_terminal for snapshot in snapshots):
            return 5.0
        return None

    @staticmethod
    def _build_admin_metrics_markdown(
        metrics_snapshot: TaskManagerMetricsSnapshot,
    ) -> str:
        status_lines = [
            f"- `{status}`: {count}"
            for status, count in sorted(metrics_snapshot.status_counts.items())
        ]
        if not status_lines:
            status_lines.append("- No tasks in memory.")

        shutdown_text = "Yes" if metrics_snapshot.is_shutting_down else "No"
        return "\n".join(
            [
                "### Admin Metrics",
                f"- Queue length: `{metrics_snapshot.queued_count}`",
                f"- Running tasks: `{metrics_snapshot.running_count}`",
                f"- In-memory tasks: `{metrics_snapshot.task_count}`",
                f"- Shutting down: `{shutdown_text}`",
                "",
                "#### Status Counts",
                *status_lines,
            ]
        )

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        return value.strftime("%H:%M:%S")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TaskDashboardViewModel",
    "TaskDashboardPresenter",
    "TaskChoice",
]
