"""Type definitions for configuration structures."""

from typing import Any, Dict, List, Optional, TypedDict


class ProviderConfig(TypedDict, total=False):
    """Type definition for a provider configuration."""
    
    # Required fields
    name: str
    type: str
    base_url: str
    api_key: str
    models: Dict[str, str]  # display_name -> model_name
    
    # Optional capability fields
    max_images: int
    aspect_ratios: List[str]
    resolutions: List[str]
    hint: Optional[str]
    max_concurrency: int


class TaskManagerConfig(TypedDict, total=False):
    """Type definition for task manager configuration."""

    max_running_tasks: int
    max_pending_tasks: int
    task_ttl_seconds: int
    running_timeout_seconds: int
    cleanup_interval_seconds: int
    shutdown_drain_timeout_seconds: int


class UIConfig(TypedDict, total=False):
    """Type definition for UI configuration."""

    theme: str
    language: str
    title: str
    show_admin_tab: bool
    

class AppConfig(TypedDict, total=False):
    """Type definition for the full application configuration."""
    
    providers: List[ProviderConfig]
    default_provider: str
    ui: Dict[str, Any]
    task_manager: TaskManagerConfig
