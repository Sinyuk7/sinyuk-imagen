"""
ui/dashboard/_internal/presenter - Task Dashboard 展示器

INTENT:
    将任务快照列表转换为 UI 可渲染的仪表盘视图模型。

SIDE EFFECT: None (纯数据转换)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from typing import List, Optional

from core.schemas import (
    BrowserTaskState,
    TaskManagerMetricsSnapshot,
    TaskSnapshot,
    TaskStatus,
)
from ui.generation._internal.status_formatter import explain_error
from ui.generation import OutputPresenter, OutputViewModel

TASK_HISTORY_STYLE = """
<style>
#task-history-list .task-history-shell,
#task-history-list .task-history-empty {
  display: grid;
  gap: 0.65rem;
}
#task-history-list .task-history-title {
  font-weight: 700;
  color: var(--body-text-color);
}
#task-history-list .task-history-hint {
  color: var(--body-text-color-subdued, var(--neutral-500));
  font-size: 0.92rem;
}
#task-history-list .task-history-row {
  position: relative;
  width: 100%;
  display: grid;
  gap: 0.34rem;
  text-align: left;
  padding: 0.8rem 0.9rem;
  border-radius: 0.9rem;
  border: 1px solid var(--block-border-color, var(--neutral-200));
  background: var(--background-fill-secondary, var(--neutral-50));
  color: var(--body-text-color);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 120ms ease, background 120ms ease, box-shadow 120ms ease;
}
#task-history-list .task-history-row::before {
  content: "";
  position: absolute;
  left: 0.38rem;
  top: 0.6rem;
  bottom: 0.6rem;
  width: 3px;
  border-radius: 999px;
  background: transparent;
}
#task-history-list .task-history-row:hover {
  border-color: var(--primary-300);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 78%, var(--primary-100) 22%);
}
#task-history-list .task-history-row.is-selected {
  border-color: var(--primary-500);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 68%, var(--primary-100) 32%);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary-500) 35%, transparent 65%);
}
#task-history-list .task-history-row.is-selected::before {
  background: var(--primary-500);
}
#task-history-list .task-history-row.is-selected:hover {
  border-color: var(--primary-500);
  background: color-mix(in srgb, var(--background-fill-secondary, white) 68%, var(--primary-100) 32%);
}
#task-history-list .task-row-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
#task-history-list .task-row-status {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--body-text-color-subdued, var(--neutral-500));
}
#task-history-list .task-row-status.status-succeeded {
  color: var(--color-green-700, #166534);
}
#task-history-list .task-row-status.status-failed {
  color: var(--color-red-700, #9f1239);
}
#task-history-list .task-row-status.status-timed-out {
  color: var(--color-amber-700, #b45309);
}
#task-history-list .task-row-status.status-running,
#task-history-list .task-row-status.status-preparing {
  color: var(--primary-700, var(--primary-500));
}
#task-history-list .task-row-prompt {
  font-weight: 600;
  line-height: 1.35;
}
#task-history-list .task-row-message {
  font-size: 0.9rem;
  line-height: 1.42;
  color: var(--body-text-color-subdued, var(--neutral-500));
}
#task-history-list .task-row-message.message-succeeded {
  color: var(--color-green-700, #166534);
}
#task-history-list .task-row-message.message-failed {
  color: var(--color-red-700, #9f1239);
}
#task-history-list .task-row-message.message-timed-out {
  color: var(--color-amber-700, #b45309);
}
#task-history-list .task-row-message.message-running {
  color: var(--primary-700, var(--primary-500));
}
#task-history-list .task-row-meta {
  color: var(--body-text-color-subdued, var(--neutral-500));
  font-size: 0.88rem;
}
#task-history-list .task-row-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}
#task-history-list .task-row-badge.unsaved {
  color: var(--color-red-700, #9f1239);
  background: color-mix(in srgb, white 75%, var(--color-red-200, #fecdd3) 25%);
}
#task-history-list .task-row-badge.saved {
  color: var(--color-green-700, #166534);
  background: color-mix(in srgb, white 72%, var(--color-green-200, #bbf7d0) 28%);
}
</style>
"""


@dataclass
class TaskDashboardViewModel:
    """UI-ready task dashboard state.
    
    INTENT: 表示任务仪表盘的完整视图状态
    """

    browser_state: BrowserTaskState = field(default_factory=BrowserTaskState)
    task_list_html: str = ""
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
        normalized_ids = [snapshot.task_id for snapshot in snapshots]
        selected_task_id = browser_state.selected_task_id
        if selected_task_id not in snapshot_map:
            selected_task_id = normalized_ids[0] if normalized_ids else None

        selected_snapshot = (
            snapshot_map.get(selected_task_id) if selected_task_id else None
        )
        detail_view_model = TaskDashboardPresenter._build_detail_view_model(
            selected_snapshot
        )
        refresh_interval = TaskDashboardPresenter._build_refresh_interval(snapshots)

        return TaskDashboardViewModel(
            browser_state=BrowserTaskState(
                task_ids=normalized_ids,
                selected_task_id=selected_task_id,
            ),
            task_list_html=TaskDashboardPresenter._build_task_list_html(
                snapshots,
                selected_task_id=selected_task_id,
            ),
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
        """Build single-line task label with fixed-width prompt.
        
        INTENT: Generate compact label for Radio choice display
        INPUT: TaskSnapshot
        OUTPUT: Single-line string with fixed-width prompt
        SIDE EFFECT: None
        FAILURE: Returns fallback label with "unknown" values
        
        Format: ✅ [UNSAVED] A beautiful sunset... | FLUX.1 | 3m
        """
        emoji = {
            TaskStatus.QUEUED: "⏳",
            TaskStatus.PREPARING: "🔧",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.SUCCEEDED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.TIMED_OUT: "⏱️",
        }.get(snapshot.status, "❓")
        saved_marker = TaskDashboardPresenter._build_saved_state_marker(snapshot)
        
        # Fixed prompt length (20 chars, padded/truncated)
        prompt = snapshot.prompt_preview or "(empty)"
        max_len = 20
        if len(prompt) > max_len:
            prompt = prompt[:max_len - 1] + "…"
        else:
            prompt = prompt.ljust(max_len)
        
        # Short model name (max 12 chars)
        model = snapshot.model or "unknown"
        if len(model) > 12:
            model = model[:11] + "…"
        
        time_str = TaskDashboardPresenter._format_relative_time_short(snapshot.submitted_at)

        if saved_marker:
            return f"{emoji} [{saved_marker}] {prompt} | {model} | {time_str}"
        return f"{emoji} {prompt} | {model} | {time_str}"

    @staticmethod
    def _build_saved_state_marker(snapshot: TaskSnapshot) -> str:
        """Return the compact saved-state marker used in task-row labels."""
        if snapshot.status != TaskStatus.SUCCEEDED or snapshot.result is None or not snapshot.result.success:
            return ""
        return "Saved" if snapshot.is_saved else "UNSAVED"

    @staticmethod
    def _build_task_list_html(
        snapshots: List[TaskSnapshot],
        *,
        selected_task_id: str | None,
    ) -> str:
        """Build the custom HTML task list used by the right-side session inbox."""
        if not snapshots:
            return (
                TASK_HISTORY_STYLE
                + '<div class="task-history-empty">'
                '<div class="task-history-title">Task History</div>'
                '<div class="task-history-hint">No tasks yet in this session. Submit your first generation to see it here.</div>'
                "</div>"
            )

        rows = [
            TaskDashboardPresenter._build_task_row_html(
                snapshot,
                selected=(snapshot.task_id == selected_task_id),
            )
            for snapshot in snapshots
        ]
        return (
            TASK_HISTORY_STYLE
            + '<div class="task-history-shell">'
            '<div class="task-history-title">Task History</div>'
            '<div class="task-history-hint">Newest first. Click a row to inspect details.</div>'
            f'{"".join(rows)}'
            "</div>"
        )

    @staticmethod
    def _build_task_row_html(snapshot: TaskSnapshot, *, selected: bool) -> str:
        """Build one clickable HTML row for the custom task list."""
        prompt = escape(snapshot.prompt_preview or "(empty prompt)")
        status_text = escape(snapshot.status.value.replace("_", " ").title())
        status_slug = escape(snapshot.status.value.replace("_", "-"))
        model = escape(snapshot.model or "unknown")
        provider = escape(snapshot.provider or "unknown")
        time_str = escape(TaskDashboardPresenter._format_relative_time_short(snapshot.submitted_at))
        message_text, message_class = TaskDashboardPresenter._build_task_row_message(snapshot)
        saved_marker = TaskDashboardPresenter._build_saved_state_marker(snapshot)
        saved_badge = ""
        if saved_marker:
            badge_class = "saved" if snapshot.is_saved else "unsaved"
            saved_badge = (
                f'<span class="task-row-badge {badge_class}">{escape(saved_marker)}</span>'
            )

        selected_attr = "true" if selected else "false"
        selected_class = " is-selected" if selected else ""
        return (
            f'<button type="button" class="task-history-row{selected_class}" '
            f'data-task-id="{escape(snapshot.task_id)}" '
            f'data-selected="{selected_attr}" '
            f'data-status="{status_text}">'
            '<span class="task-row-topline">'
            f'<span class="task-row-status status-{status_slug}">{status_text}</span>'
            f'{saved_badge}'
            "</span>"
            f'<span class="task-row-prompt">{prompt}</span>'
            f'<span class="task-row-message {escape(message_class)}">{escape(message_text)}</span>'
            f'<span class="task-row-meta">{provider} · {model} · {time_str}</span>'
            "</button>"
        )

    @staticmethod
    def _build_task_row_message(snapshot: TaskSnapshot) -> tuple[str, str]:
        """Build the short secondary message shown inside a task row."""
        if snapshot.status == TaskStatus.SUCCEEDED:
            if snapshot.is_saved:
                return ("Marked saved for this session.", "message-succeeded")
            return (
                "Images are ready in this session. Download them before leaving.",
                "message-succeeded",
            )
        if snapshot.status == TaskStatus.FAILED:
            return (
                explain_error(
                    snapshot.error or "Task failed.",
                    snapshot.error_code,
                ),
                "message-failed",
            )
        if snapshot.status == TaskStatus.TIMED_OUT:
            return (
                explain_error(
                    snapshot.error or "Task timed out.",
                    snapshot.error_code,
                ),
                "message-timed-out",
            )
        if snapshot.status == TaskStatus.RUNNING:
            return (
                "Generating now. This task is still safe in the current session.",
                "message-running",
            )
        if snapshot.status == TaskStatus.PREPARING:
            return ("Preparing files for the provider request.", "message-running")
        return ("Waiting for an available worker slot.", "")

    @staticmethod
    def _format_relative_time_short(dt: Optional[datetime]) -> str:
        """Convert timestamp to short relative time (e.g., '3m', '2h', '1d')."""
        if dt is None:
            return "?"
        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "now"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"

    @staticmethod
    def _format_relative_time(dt: Optional[datetime]) -> str:
        """Convert timestamp to relative time (e.g., '3 min ago')."""
        if dt is None:
            return "unknown"
        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins} min ago" if mins == 1 else f"{mins} mins ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hr ago" if hours == 1 else f"{hours} hrs ago"
        else:
            days = seconds // 86400
            return f"{days} day ago" if days == 1 else f"{days} days ago"

    @staticmethod
    def _build_refresh_interval(snapshots: List[TaskSnapshot]) -> Optional[float]:
        if any(snapshot.status == TaskStatus.RUNNING for snapshot in snapshots):
            return 2.0
        if any(not snapshot.is_terminal for snapshot in snapshots):
            return 5.0
        if snapshots:
            return 60.0
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
]
