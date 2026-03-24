"""Configuration validation logic."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, cast

from .defaults import (
    DEFAULT_ASPECT_RATIOS,
    DEFAULT_MAX_IMAGES,
    REQUIRED_PROVIDER_FIELDS,
)
from .errors import ConfigError

logger = logging.getLogger(__name__)


class ProviderValidator(ABC):
    """Abstract base validator for provider configurations.
    
    Subclass this to create custom validation rules for specific provider types.
    """
    
    @abstractmethod
    def validate(self, provider: Dict[str, Any]) -> List[str]:
        """Validate a provider configuration.
        
        Args:
            provider: Provider configuration dictionary.
            
        Returns:
            List of validation error messages. Empty list if valid.
        """
        pass


class DefaultProviderValidator(ProviderValidator):
    """Default validation rules applicable to all providers."""
    
    def validate(self, provider: Dict[str, Any]) -> List[str]:
        """Validate required fields and optional capability fields."""
        errors: List[str] = []
        
        # Check required fields
        for field_name in REQUIRED_PROVIDER_FIELDS:
            if field_name not in provider or provider[field_name] is None:
                errors.append(f"Missing required field: '{field_name}'")
        
        # Validate models is a non-empty dict
        models_val: Any = provider.get("models")
        if not isinstance(models_val, dict) or len(cast(Dict[str, Any], models_val)) == 0:
            example = (
                "models:\n"
                "  \"Gemini 2.5 Flash (Preview Image Gen)\": gemini-2.5-flash-preview-image-generation\n"
            )
            errors.append(
                f"'models' must be a non-empty mapping (display_name -> model_name).\n"
                f"Example:\n{example}"
            )
        elif not all(
            isinstance(display_name, str)
            and display_name.strip()
            and isinstance(model_name, str)
            and model_name.strip()
            for display_name, model_name in cast(Dict[str, Any], models_val).items()
        ):
            errors.append(
                "'models' must map non-empty display_name strings "
                "to non-empty model_name strings"
            )
        
        # Validate optional capability fields
        errors.extend(self._validate_optional_fields(provider))
        
        return errors
    
    @staticmethod
    def _validate_optional_fields(provider: Dict[str, Any]) -> List[str]:
        """Validate optional provider capability fields."""
        errors: List[str] = []
        
        if "max_images" in provider:
            val = provider["max_images"]
            if not isinstance(val, int) or val < 1:
                errors.append(f"'max_images' must be a positive integer, got: {val!r}")

        if "api_version" in provider:
            val = provider["api_version"]
            if not isinstance(val, str) or not val.strip():
                errors.append(f"'api_version' must be a non-empty string, got: {val!r}")
        
        if "aspect_ratios" in provider:
            val = provider["aspect_ratios"]
            if not isinstance(val, list) or not all(isinstance(item, str) for item in val):
                errors.append(f"'aspect_ratios' must be a list of strings, got: {val!r}")
        
        if "resolutions" in provider:
            val = provider["resolutions"]
            if not isinstance(val, list) or not all(isinstance(item, str) for item in val):
                errors.append(f"'resolutions' must be a list of strings, got: {val!r}")
        
        if "hint" in provider:
            val = provider["hint"]
            if val is not None and (not isinstance(val, str) or not val.strip()):
                errors.append(f"'hint' must be a non-empty string or null, got: {val!r}")

        if "max_concurrency" in provider:
            val = provider["max_concurrency"]
            if not isinstance(val, int) or val < 1:
                errors.append(f"'max_concurrency' must be a positive integer, got: {val!r}")
        
        return errors


class ConfigValidator:
    """Main validator that orchestrates configuration validation."""
    
    def __init__(self) -> None:
        self._provider_validators: List[ProviderValidator] = [DefaultProviderValidator()]
    
    def register_provider_validator(self, validator: ProviderValidator) -> None:
        """Register an additional provider validator.
        
        Allows extending validation with custom rules for specific provider types.
        """
        self._provider_validators.append(validator)
    
    def validate(self, config: Dict[str, Any]) -> None:
        """Validate the entire configuration.
        
        Args:
            config: Parsed configuration dictionary.
            
        Raises:
            ConfigError: If validation fails.
        """
        providers: Any = config.get("providers")
        if not providers or not isinstance(providers, list):
            raise ConfigError("'providers' must be a non-empty list in config.yaml")
        
        providers_list = cast(List[Any], providers)
        
        # Validate each provider
        for i, p in enumerate(providers_list):
            if not isinstance(p, dict):
                raise ConfigError(f"Provider entry {i} must be a mapping")
            
            p_dict = cast(Dict[str, Any], p)
            provider_name = str(p_dict.get("name", f"index {i}"))
            
            # Run all registered validators
            all_errors: List[str] = []
            for validator in self._provider_validators:
                all_errors.extend(validator.validate(p_dict))
            
            if all_errors:
                error_msg = "\n".join(f"  - {e}" for e in all_errors)
                raise ConfigError(f"Provider '{provider_name}' validation failed:\n{error_msg}")
        
        # Check unique provider names
        names: List[str] = [str(p["name"]) for p in providers_list]
        if len(names) != len(set(names)):
            duplicates: List[str] = [n for n in names if names.count(n) > 1]
            raise ConfigError(f"Duplicate provider names detected: {set(duplicates)}")
        
        # Check default_provider references valid provider
        default = config.get("default_provider")
        if not default:
            raise ConfigError("'default_provider' must be set in config.yaml")
        if default not in names:
            raise ConfigError(
                f"'default_provider' references '{default}', "
                f"which is not a configured provider. Available: {names}"
            )

        task_manager = config.get("task_manager")
        if task_manager is not None:
            if not isinstance(task_manager, dict):
                raise ConfigError("'task_manager' must be a mapping if provided")
            for field_name in (
                "max_running_tasks",
                "max_pending_tasks",
                "task_ttl_seconds",
                "running_timeout_seconds",
                "cleanup_interval_seconds",
                "shutdown_drain_timeout_seconds",
            ):
                if field_name not in task_manager:
                    continue
                value = task_manager[field_name]
                if not isinstance(value, int) or value < 1:
                    raise ConfigError(
                        f"'task_manager.{field_name}' must be a positive integer, got: {value!r}"
                    )

        ui_config = config.get("ui")
        if ui_config is not None:
            if not isinstance(ui_config, dict):
                raise ConfigError("'ui' must be a mapping if provided")
            if "show_admin_tab" in ui_config and not isinstance(ui_config["show_admin_tab"], bool):
                raise ConfigError("'ui.show_admin_tab' must be a boolean if provided")

        logger.info("Configuration validation passed")
