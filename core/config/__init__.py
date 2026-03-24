"""Configuration management module.

This module provides configuration loading, validation, and access APIs.

Example:
    from core.config import ConfigManager
    
    config = ConfigManager()
    provider = config.get_active_provider()
    models = config.get_models(config.get_active_provider_name())
"""

from .config_manager import ConfigManager
from .defaults import (
    DEFAULT_ASPECT_RATIOS,
    DEFAULT_MAX_IMAGES,
    DEFAULT_TASK_MANAGER_CONFIG,
    REQUIRED_PROVIDER_FIELDS,
)
from .errors import ConfigError
from .loader import ConfigLoader
from .schema import AppConfig, ProviderConfig, TaskManagerConfig, UIConfig
from .validator import ConfigValidator, DefaultProviderValidator, ProviderValidator

__all__ = [
    # Main class
    "ConfigManager",
    # Exceptions
    "ConfigError",
    # Components
    "ConfigLoader",
    "ConfigValidator",
    "ProviderValidator",
    "DefaultProviderValidator",
    # Defaults
    "DEFAULT_ASPECT_RATIOS",
    "DEFAULT_MAX_IMAGES",
    "DEFAULT_TASK_MANAGER_CONFIG",
    "REQUIRED_PROVIDER_FIELDS",
    # Schema types
    "AppConfig",
    "ProviderConfig",
    "TaskManagerConfig",
    "UIConfig",
]
