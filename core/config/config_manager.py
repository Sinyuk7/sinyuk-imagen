"""Configuration management: load config.yaml, provide access APIs."""

import logging
from typing import Any, Dict, List, Optional, cast

from .defaults import (
    DEFAULT_ASPECT_RATIOS,
    DEFAULT_MAX_IMAGES,
    DEFAULT_RESOLUTIONS,
    DEFAULT_TASK_MANAGER_CONFIG,
    DEFAULT_UI_CONFIG,
)
from .errors import ConfigError
from .loader import ConfigLoader
from .validator import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """Loads, validates, and provides access to application configuration.

    Responsibilities:
    - Load config.yaml and resolve ${VAR} environment variable references
    - Validate provider definitions at startup
    - Provide query APIs for providers, models, and default provider
    - Provide query APIs for provider capabilities (max_images, aspect_ratios, resolutions)
    - Support in-memory active provider switching (no file write)
    
    Example:
        config = ConfigManager()
        provider = config.get_active_provider()
        models = config.get_models(config.get_active_provider_name())
    """

    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        # 1. Load configuration
        loader = ConfigLoader()
        self._raw = loader.load(config_path, env_path)
        
        # 2. Validate configuration
        validator = ConfigValidator()
        validator.validate(self._raw)
        
        # 3. Initialize internal state
        self._providers: Dict[str, Dict[str, Any]] = {
            p["name"]: p for p in self._raw["providers"]
        }
        self._active_provider: str = self._raw["default_provider"]

        logger.info(
            "ConfigManager initialized: %d providers, default=%s",
            len(self._providers),
            self._active_provider,
        )

    # ── Public query APIs ──────────────────────────────────────────

    def get_active_provider(self) -> Dict[str, Any]:
        """Return the config dict of the currently active provider."""
        return self._providers[self._active_provider]

    def get_active_provider_name(self) -> str:
        """Return the name of the currently active provider."""
        return self._active_provider

    def get_provider(self, name: str) -> Dict[str, Any]:
        """Return config dict for a specific provider by name."""
        if name not in self._providers:
            raise ConfigError(f"Provider '{name}' not found in configuration")
        return self._providers[name]

    def get_provider_names(self) -> List[str]:
        """Return list of all configured provider names."""
        return list(self._providers.keys())

    def get_models(self, provider_name: str) -> List[str]:
        """Return list of model display names for a given provider.

        Provider `models` MUST be a dict mapping: `display_name -> model_name`.
        UI consumes display names; provider layer maps to real model names.
        """
        provider = self.get_provider(provider_name)
        models_val: Any = provider.get("models", {})
        if not isinstance(models_val, dict):
            raise ConfigError(
                f"Provider '{provider_name}': 'models' must be a mapping of display_name -> model_name"
            )
        return list(cast(Dict[str, Any], models_val).keys())

    def get_model_name(self, provider_name: str, display_name: str) -> str:
        """Resolve a model display name to the real model name for a provider."""
        provider = self.get_provider(provider_name)
        models_val: Any = provider.get("models", {})
        if not isinstance(models_val, dict):
            raise ConfigError(
                f"Provider '{provider_name}': 'models' must be a mapping of display_name -> model_name"
            )
        models_map = cast(Dict[str, Any], models_val)
        if display_name not in models_map:
            raise ConfigError(
                f"Provider '{provider_name}': unknown model display name '{display_name}'. "
                f"Available: {list(models_map.keys())}"
            )
        return str(models_map[display_name])

    def get_provider_hint(self, provider_name: str) -> Optional[str]:
        """Return optional provider hint for prompt placeholder."""
        provider = self.get_provider(provider_name)
        hint = provider.get("hint")
        if hint is None:
            return None
        return str(hint)

    def get_ui_config(self) -> Dict[str, Any]:
        """Return UI configuration section."""
        ui_config = dict(DEFAULT_UI_CONFIG)
        configured = self._raw.get("ui", {})
        if isinstance(configured, dict):
            ui_config.update(configured)
        return ui_config

    def get_task_manager_config(self) -> Dict[str, Any]:
        """Return task manager config with defaults applied."""
        task_manager = dict(DEFAULT_TASK_MANAGER_CONFIG)
        configured = self._raw.get("task_manager", {})
        if isinstance(configured, dict):
            task_manager.update(configured)
        return task_manager

    # ── Provider capability query APIs ─────────────────────────────

    def get_max_images(self, provider_name: str) -> int:
        """Return the maximum number of images for a provider. Default: 1."""
        provider = self.get_provider(provider_name)
        return int(provider.get("max_images", DEFAULT_MAX_IMAGES))

    def get_aspect_ratios(self, provider_name: str) -> List[str]:
        """Return the aspect ratio options for a provider. Default: standard list."""
        provider = self.get_provider(provider_name)
        return list(provider.get("aspect_ratios", DEFAULT_ASPECT_RATIOS))

    def get_resolutions(self, provider_name: str) -> List[str]:
        """Return the resolution options for a provider. Default: ["1K", "2K", "4K"]."""
        provider = self.get_provider(provider_name)
        return list(provider.get("resolutions", DEFAULT_RESOLUTIONS))

    def get_provider_max_concurrency(self, provider_name: str) -> Optional[int]:
        """Return optional provider-level concurrency limit."""
        provider = self.get_provider(provider_name)
        value = provider.get("max_concurrency")
        if value is None:
            return None
        return int(value)

    # ── Runtime state mutation ─────────────────────────────────────

    def set_active_provider(self, name: str) -> None:
        """Switch active provider in-memory. Does NOT write to config file."""
        if name not in self._providers:
            raise ConfigError(
                f"Cannot set active provider to '{name}': not found in configuration"
            )
        logger.info("Active provider changed: %s -> %s", self._active_provider, name)
        self._active_provider = name
