"""Tests for task dashboard action button behavior."""

from datetime import datetime, timezone

from core.schemas import TaskSnapshot, TaskStatus
from ui.dashboard._internal.handler import TaskDashboardHandler


def build_snapshot(*, status: TaskStatus, is_saved: bool) -> TaskSnapshot:
    return TaskSnapshot(
        task_id="task-1",
        status=status,
        provider="provider",
        model="Nano Banana 2",
        prompt_preview="A cinematic cat portrait",
        submitted_at=datetime.now(timezone.utc),
        result=type("Result", (), {"success": True})(),
        is_saved=is_saved,
    )


def test_mark_saved_button_stays_visible_but_disabled_for_failed_task() -> None:
    handler = TaskDashboardHandler()

    update = handler._build_mark_saved_button_update(
        build_snapshot(status=TaskStatus.FAILED, is_saved=False),
    )

    assert update["visible"] is True
    assert update["interactive"] is False


def test_mark_saved_button_is_enabled_for_unsaved_success() -> None:
    handler = TaskDashboardHandler()

    update = handler._build_mark_saved_button_update(
        build_snapshot(status=TaskStatus.SUCCEEDED, is_saved=False),
    )

    assert update["visible"] is True
    assert update["interactive"] is True
