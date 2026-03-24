"""Private runtime singleton management for the core facade."""

from __future__ import annotations

from dataclasses import dataclass

from core.config import ConfigManager
from core.generation.entry import ImageGenerationService
from core.schemas import TaskManagerSettings
from core.tasking.entry import TaskManager


@dataclass
class Runtime:
    """Own the long-lived runtime services behind the public facade."""

    config_manager: ConfigManager
    image_service: ImageGenerationService
    task_manager: TaskManager


_runtime: Runtime | None = None


def initialize_runtime(config_path: str = "config.yaml", env_path: str = ".env") -> None:
    """Initialize the shared runtime singleton used by the public facade."""
    global _runtime
    config_manager = ConfigManager(config_path=config_path, env_path=env_path)
    image_service = ImageGenerationService(config_manager)
    task_manager = TaskManager(
        image_service,
        settings=TaskManagerSettings(**config_manager.get_task_manager_config()),
    )
    _runtime = Runtime(
        config_manager=config_manager,
        image_service=image_service,
        task_manager=task_manager,
    )


def get_runtime() -> Runtime:
    """Return the initialized runtime, creating it on first access."""
    global _runtime
    if _runtime is None:
        initialize_runtime()
    assert _runtime is not None
    return _runtime
