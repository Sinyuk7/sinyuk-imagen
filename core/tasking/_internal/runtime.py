"""Private task runtime owning background async execution."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import threading
import time
from typing import TYPE_CHECKING

from core.schemas import TaskConfig
from core.schemas import TaskErrorCode
from core.schemas import TaskManagerSettings

from .artifacts import TaskArtifactStore
from .exceptions import InvalidTaskTransition
from .policies import ProviderConcurrencyPolicy
from .store import TaskStore

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from core.generation.entry import ImageGenerationService


class TaskRuntime:
    """Run queued tasks on a private event loop with async providers."""

    def __init__(
        self,
        *,
        image_service: "ImageGenerationService",
        store: TaskStore,
        artifact_store: TaskArtifactStore,
        settings: TaskManagerSettings,
        provider_policy: ProviderConcurrencyPolicy,
    ) -> None:
        self._image_service = image_service
        self._store = store
        self._artifact_store = artifact_store
        self._settings = settings
        self._provider_policy = provider_policy
        self._started = threading.Event()
        self._closed = threading.Event()
        self._shutdown = threading.Event()
        self._shutdown_reason = "Task manager is shutting down. Please try again later."
        self._thread = threading.Thread(
            target=self._run_loop,
            name="sinyuk-imagen-task-manager",
            daemon=True,
        )
        self._thread.start()
        self._started.wait()

    @property
    def shutdown_reason(self) -> str:
        return self._shutdown_reason

    def is_shutting_down(self) -> bool:
        return self._shutdown.is_set()

    def enqueue_task(self, task_id: str, task_config: TaskConfig) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (task_id, task_config))

    def begin_shutdown(self, *, reason: str) -> None:
        if self._shutdown.is_set():
            return

        self._shutdown_reason = reason
        self._shutdown.set()
        cleanup_paths = self._store.fail_pending_for_shutdown(now=self._utcnow(), reason=reason)
        if cleanup_paths:
            self._artifact_store.cleanup_paths(cleanup_paths)

    def close(self) -> None:
        if self._closed.is_set():
            return

        self.begin_shutdown(reason=self._shutdown_reason)
        deadline = time.monotonic() + self._settings.shutdown_drain_timeout_seconds
        while time.monotonic() < deadline:
            if not self._store.has_running_tasks():
                break
            time.sleep(0.05)

        self._closed.set()
        if hasattr(self, "_loop"):
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._queue: asyncio.Queue[tuple[str, TaskConfig]] = asyncio.Queue()
        self._provider_semaphores = {
            provider_name: asyncio.Semaphore(limit)
            for provider_name, limit in self._provider_policy.limits.items()
        }
        self._worker_tasks = [
            self._loop.create_task(self._worker()) for _ in range(self._settings.max_running_tasks)
        ]
        self._cleanup_task = self._loop.create_task(self._cleanup_loop())
        self._started.set()
        try:
            self._loop.run_forever()
        finally:
            for task in self._worker_tasks:
                task.cancel()
            self._cleanup_task.cancel()
            self._loop.run_until_complete(
                asyncio.gather(*self._worker_tasks, self._cleanup_task, return_exceptions=True)
            )
            self._loop.close()
            asyncio.set_event_loop(None)

    async def _worker(self) -> None:
        while True:
            task_id, task_config = await self._queue.get()
            try:
                await self._run_one_task(task_id, task_config)
            finally:
                self._queue.task_done()

    async def _run_one_task(self, task_id: str, task_config: TaskConfig) -> None:
        # STEP 1: move queued work into the execution lane only while it is live.
        if self.is_shutting_down():
            self._fail_task_for_shutdown(task_id)
            return
        if not self._store.mark_preparing(task_id):
            return

        semaphore = self._provider_semaphores.get(task_config.provider)
        if semaphore is None:
            await self._execute_task(task_id, task_config)
            return

        async with semaphore:
            if self.is_shutting_down():
                self._fail_task_for_shutdown(task_id)
                return
            await self._execute_task(task_id, task_config)

    async def _execute_task(self, task_id: str, task_config: TaskConfig) -> None:
        # STEP 2: claim a lease before crossing into the async provider boundary.
        start = self._store.start_attempt(
            task_id,
            now=self._utcnow(),
            shutdown_reason=self.shutdown_reason if self.is_shutting_down() else None,
        )
        if start.cleanup_paths:
            self._artifact_store.cleanup_paths(start.cleanup_paths)
        if start.attempt_id is None:
            return

        try:
            result = await self._run_generation(task_config)
        except asyncio.TimeoutError:
            logger.error(
                "Task %s timed out after %ss",
                task_id,
                self._settings.running_timeout_seconds,
            )
            cleanup_paths = self._store.finish_timeout(
                task_id,
                attempt_id=start.attempt_id,
                now=self._utcnow(),
                error_message="Task execution timed out.",
            )
            if cleanup_paths:
                self._artifact_store.cleanup_paths(cleanup_paths)
            return
        except Exception as exc:
            logger.exception("Task %s crashed unexpectedly: %s", task_id, exc)
            self._store.finish_failure(
                task_id,
                attempt_id=start.attempt_id,
                now=self._utcnow(),
                error_message=str(exc),
                error_code=TaskErrorCode.PROVIDER_ERROR,
            )
            return

        await self._commit_result(task_id, start.attempt_id, result)

    async def _run_generation(self, task_config: TaskConfig):
        return await asyncio.wait_for(
            self._image_service.generate(task_config),
            timeout=self._settings.running_timeout_seconds,
        )

    async def _commit_result(self, task_id: str, attempt_id: int, result) -> None:
        try:
            materialized = self._artifact_store.materialize_result(task_id, result)
        except Exception as exc:
            logger.exception("Task %s failed while materializing outputs: %s", task_id, exc)
            self._store.finish_failure(
                task_id,
                attempt_id=attempt_id,
                now=self._utcnow(),
                error_message=f"Failed to stage task results: {exc}",
                error_code=TaskErrorCode.RESULT_MATERIALIZATION_FAILED,
            )
            return

        cleanup_paths = self._store.finish_success(
            task_id,
            attempt_id=attempt_id,
            now=self._utcnow(),
            result=materialized.result,
            result_paths=materialized.related_files,
        )
        if cleanup_paths:
            self._artifact_store.cleanup_paths(cleanup_paths)

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(self._settings.cleanup_interval_seconds)
            self._cleanup_expired_tasks()

    def _cleanup_expired_tasks(self) -> None:
        cleanup = self._store.collect_expired(
            now=self._utcnow(),
            running_timeout_seconds=self._settings.running_timeout_seconds,
            task_ttl_seconds=self._settings.task_ttl_seconds,
            session_ttl_seconds=self._settings.session_ttl_seconds,
        )
        if cleanup.paths_to_cleanup:
            self._artifact_store.cleanup_paths(cleanup.paths_to_cleanup)
        for task_id in cleanup.expired_task_ids:
            related_files = self._store.delete_task(task_id)
            self._artifact_store.delete_task(task_id, related_files)

    def _fail_task_for_shutdown(self, task_id: str) -> None:
        try:
            cleanup_paths = self._store.fail_task_for_shutdown(
                task_id,
                now=self._utcnow(),
                reason=self.shutdown_reason,
            )
        except InvalidTaskTransition:
            return
        if cleanup_paths:
            self._artifact_store.cleanup_paths(cleanup_paths)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)
