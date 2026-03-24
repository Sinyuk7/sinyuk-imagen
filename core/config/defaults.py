"""Default values for optional provider capability fields."""

# Default maximum number of images per request
DEFAULT_MAX_IMAGES = 1

# Default supported aspect ratios
DEFAULT_ASPECT_RATIOS = ["1:1", "3:4", "2:3", "9:16", "9:21"]

# Default supported resolutions
DEFAULT_RESOLUTIONS = ["1K","2K", "4K"]

# Default task manager settings
DEFAULT_TASK_MANAGER_CONFIG = {
    "max_running_tasks": 2,
    "max_pending_tasks": 20,
    "task_ttl_seconds": 10800,
    "running_timeout_seconds": 3600,
    "cleanup_interval_seconds": 600,
    "shutdown_drain_timeout_seconds": 10,
}

# Default UI settings
DEFAULT_UI_CONFIG = {
    "show_admin_tab": True,
}

# Required fields for each provider configuration
REQUIRED_PROVIDER_FIELDS = ("name", "type", "base_url", "api_key", "models")
