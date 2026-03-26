"""Tests for compact task-row labels in the dashboard presenter."""

from datetime import datetime, timezone

from core.schemas import TaskErrorCode, TaskSnapshot, TaskStatus
from ui.dashboard._internal.presenter import TaskDashboardPresenter


def build_snapshot(*, is_saved: bool) -> TaskSnapshot:
    return TaskSnapshot(
        task_id="task-1",
        status=TaskStatus.SUCCEEDED,
        provider="provider",
        model="Nano Banana 2",
        prompt_preview="A cinematic cat portrait",
        submitted_at=datetime.now(timezone.utc),
        result=type("Result", (), {"success": True})(),
        is_saved=is_saved,
    )


def test_task_choice_label_marks_unsaved_successes() -> None:
    label = TaskDashboardPresenter._build_task_choice_label(build_snapshot(is_saved=False))
    assert "[UNSAVED]" in label


def test_task_choice_label_marks_saved_successes() -> None:
    label = TaskDashboardPresenter._build_task_choice_label(build_snapshot(is_saved=True))
    assert "[Saved]" in label


def test_task_row_html_shows_failure_reason_in_row() -> None:
    snapshot = TaskSnapshot(
        task_id="task-failed",
        status=TaskStatus.FAILED,
        provider="provider",
        model="Nano Banana 2",
        prompt_preview="A cinematic cat portrait",
        submitted_at=datetime.now(timezone.utc),
        error="401 Unauthorized: invalid api key",
        error_code=TaskErrorCode.PROVIDER_ERROR,
    )

    html = TaskDashboardPresenter._build_task_row_html(snapshot, selected=True)

    assert "Your API key looks invalid" in html
    assert "message-failed" in html
    assert "is-selected" in html
