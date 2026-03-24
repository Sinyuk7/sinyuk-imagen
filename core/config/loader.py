"""Configuration loading: YAML file parsing and environment variable resolution."""

import logging
import os
import re
from pathlib import Path
from typing import Any, cast

import yaml
from dotenv import load_dotenv

from .errors import ConfigError

logger = logging.getLogger(__name__)

# Pattern for ${VAR} environment variable references
_ENV_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")

class ConfigLoader:
    """Handles YAML loading and environment variable resolution."""
    
    def load(self, config_path: str, env_path: str) -> dict[str, Any]:
        """Load config from YAML file and resolve environment variables.
        
        Args:
            config_path: Path to the YAML configuration file.
            env_path: Path to the .env file for environment variables.
            
        Returns:
            Parsed configuration dictionary with environment variables resolved.
            
        Raises:
            ConfigError: If config file not found or invalid YAML.
        """
        load_dotenv(env_path)
        raw = self._load_yaml(config_path)
        self._normalize_legacy_root_keys(raw)
        self._resolve_env_vars(raw)
        return raw
    
    @staticmethod
    def _load_yaml(path: str) -> dict[str, Any]:
        """Load and parse YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {path}")
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ConfigError(f"Configuration file must be a YAML mapping: {path}")
        return cast(dict[str, Any], data)

    @staticmethod
    def _normalize_legacy_root_keys(config: dict[str, Any]) -> None:
        """Normalize legacy root-level keys in-place."""
        if "default_provider" in config or "active_provider" not in config:
            return

        logger.warning(
            "Legacy config key 'active_provider' detected; please rename it to 'default_provider'."
        )
        config["default_provider"] = config["active_provider"]
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve ${VAR} references in config values.
        
        Modifies the config dict in-place.
        
        Raises:
            ConfigError: If referenced environment variable is not set.
        """
        if isinstance(obj, str):
            match = _ENV_VAR_PATTERN.fullmatch(obj.strip())
            if match:
                var_name = match.group(1)
                value = os.environ.get(var_name)
                if value is None:
                    raise ConfigError(
                        f"Environment variable '{var_name}' is not set. "
                        f"Check your .env file or system environment."
                    )
                return value
            return obj
        elif isinstance(obj, dict):
            d = cast(dict[str, Any], obj)
            for key in list(d.keys()):
                d[key] = self._resolve_env_vars(d[key])
            return d
        elif isinstance(obj, list):
            lst = cast(list[Any], obj)
            for i, item in enumerate(lst):
                lst[i] = self._resolve_env_vars(item)
            return lst
        return obj
