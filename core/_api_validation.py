"""Private validation helpers for the core facade."""

from __future__ import annotations

from core._api_ui_context import build_ui_context
from core.config import ConfigManager
from core.schemas import TaskConfig, UIContext


def validate_task_config(config_manager: ConfigManager, config: TaskConfig) -> TaskConfig:
    """Reject invalid UI-built task configs before they enter core execution."""
    prompt = config.prompt.strip()
    if not prompt:
        raise ValueError("Prompt must not be empty.")

    ui_context = build_ui_context(config_manager)
    validate_provider_id(config_manager, config.provider)
    validate_model_display_name(config_manager, config.provider, config.model)
    validate_divisible_by(config.divisible_by)
    validate_reference_image_path(config.reference_image_path)
    validate_image_count(config_manager, config.provider, config.params.get("image_count"))
    validate_optional_aspect_ratio(
        ui_context,
        config.provider,
        config.params.get("aspect_ratio"),
    )
    validate_optional_resolution(
        ui_context,
        config.provider,
        config.params.get("resolution"),
    )
    return config


def validate_provider_id(config_manager: ConfigManager, provider: str) -> None:
    """Validate that the selected provider is configured."""
    if provider not in config_manager.get_provider_names():
        raise ValueError(f"Provider '{provider}' is not configured.")


def validate_model_display_name(
    config_manager: ConfigManager,
    provider: str,
    model: str,
) -> None:
    """Validate that the selected model belongs to the selected provider."""
    if model not in config_manager.get_models(provider):
        raise ValueError(f"Model '{model}' is not available for provider '{provider}'.")


def validate_image_count(
    config_manager: ConfigManager,
    provider: str,
    image_count: object,
) -> None:
    """Validate that image_count is an integer within provider limits."""
    if image_count is None:
        return
    if not isinstance(image_count, int):
        raise ValueError("image_count must be an integer.")
    if image_count < 1:
        raise ValueError("image_count must be at least 1.")
    max_images = config_manager.get_max_images(provider)
    if image_count > max_images:
        raise ValueError(
            f"image_count must not exceed {max_images} for provider '{provider}'."
        )


def _flip_aspect_ratio(ratio: str) -> str:
    """Flip an aspect ratio string, e.g., '2:3' -> '3:2'."""
    if ":" not in ratio:
        return ratio
    parts = ratio.split(":")
    if len(parts) != 2:
        return ratio
    return f"{parts[1]}:{parts[0]}"


def _is_aspect_ratio_supported(ratio: str, supported_ratios: tuple[str, ...] | list[str]) -> bool:
    """Check if ratio or its flipped version is in the supported list.
    
    Provider configs define base ratios (e.g., '2:3'), but both the base
    and flipped versions (e.g., '3:2') are considered valid.
    """
    if ratio in supported_ratios:
        return True
    flipped = _flip_aspect_ratio(ratio)
    return flipped in supported_ratios


def validate_optional_aspect_ratio(
    ui_context: UIContext,
    provider: str,
    aspect_ratio: object,
) -> None:
    """Validate a provider-specific aspect ratio token when present.
    
    Both the configured ratio and its flipped version are accepted.
    For example, if provider supports '2:3', then '3:2' is also valid.
    """
    if aspect_ratio is None:
        return
    if not isinstance(aspect_ratio, str) or not aspect_ratio.strip():
        raise ValueError("aspect_ratio must be a non-empty string when provided.")
    if aspect_ratio == "original":
        return
    provider_context = ui_context.get_provider(provider)
    if not _is_aspect_ratio_supported(aspect_ratio, provider_context.aspect_ratios):
        raise ValueError(
            f"aspect_ratio '{aspect_ratio}' is not available for provider '{provider}'."
        )


def validate_known_aspect_ratio(
    ui_context: UIContext,
    aspect_ratio: object,
) -> None:
    """Validate that the aspect ratio exists for at least one configured provider.
    
    Both the configured ratio and its flipped version are accepted.
    """
    if aspect_ratio is None:
        return
    if not isinstance(aspect_ratio, str) or not aspect_ratio.strip():
        raise ValueError("aspect_ratio must be a non-empty string when provided.")
    if aspect_ratio == "original":
        return
    for provider_context in ui_context.providers.values():
        if _is_aspect_ratio_supported(aspect_ratio, provider_context.aspect_ratios):
            return
    raise ValueError(f"aspect_ratio '{aspect_ratio}' is not configured for any provider.")


def validate_optional_resolution(
    ui_context: UIContext,
    provider: str,
    resolution: object,
) -> None:
    """Validate a provider-specific resolution token when present."""
    if resolution is None:
        return
    if not isinstance(resolution, str) or not resolution.strip():
        raise ValueError("resolution must be a non-empty string when provided.")
    provider_context = ui_context.get_provider(provider)
    if resolution not in provider_context.resolutions:
        raise ValueError(
            f"resolution '{resolution}' is not available for provider '{provider}'."
        )


def validate_divisible_by(divisible_by: int) -> None:
    """Validate that divisible_by is a positive integer."""
    if not isinstance(divisible_by, int) or divisible_by < 1:
        raise ValueError("divisible_by must be a positive integer.")


def validate_reference_image_path(reference_image_path: str | None) -> None:
    """Validate that a reference image path is a non-empty string when provided."""
    if reference_image_path is None:
        return
    if not isinstance(reference_image_path, str) or not reference_image_path.strip():
        raise ValueError("reference_image_path must be a non-empty string when provided.")
