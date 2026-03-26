"""Tests for session-owned save state in the task store."""

from datetime import datetime, timedelta, timezone

from core.schemas import GenerationResult, TaskConfig
from core.tasking._internal.store import TaskStore


def test_mark_all_tasks_saved_marks_successful_session_tasks() -> None:
    store = TaskStore()
    now = datetime.now(timezone.utc)
    session_id = "session-1"

    first_task_id = "task-1"
    second_task_id = "task-2"
    config = TaskConfig(prompt="A cat", provider="provider", model="model")

    for task_id in (first_task_id, second_task_id):
        store.create_task(
            task_id,
            config,
            owner_session_id=session_id,
            now=now,
            related_files=[],
            max_pending_tasks=20,
            is_shutting_down=False,
            shutdown_reason="",
        )
        assert store.mark_preparing(task_id) is True
        attempt = store.start_attempt(task_id, now=now)
        assert attempt.attempt_id is not None
        store.finish_success(
            task_id,
            attempt_id=attempt.attempt_id,
            now=now,
            result=GenerationResult(images=[], provider="provider", model="model"),
            result_paths=[],
        )

    updated = store.mark_all_tasks_saved(owner_session_id=session_id, now=now)

    snapshots = store.list_snapshots_for_session(session_id)
    assert updated == 2
    assert all(snapshot.is_saved for snapshot in snapshots)


def test_collect_expired_reclaims_stale_session_queued_tasks() -> None:
    store = TaskStore()
    created_at = datetime.now(timezone.utc) - timedelta(hours=13)
    session_id = "session-stale"

    store.create_task(
        "task-stale",
        TaskConfig(prompt="A cat", provider="provider", model="model"),
        owner_session_id=session_id,
        now=created_at,
        related_files=[],
        max_pending_tasks=20,
        is_shutting_down=False,
        shutdown_reason="",
    )

    cleanup = store.collect_expired(
        now=datetime.now(timezone.utc),
        running_timeout_seconds=3600,
        task_ttl_seconds=3600,
        session_ttl_seconds=43200,
    )

    assert "task-stale" in cleanup.expired_task_ids
