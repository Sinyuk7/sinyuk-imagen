"""Private UI-context builders for the core facade."""

from __future__ import annotations

from core.config import ConfigManager
from core.schemas import ProviderUIContext, UIContext


def build_provider_context(
    config_manager: ConfigManager,
    provider_name: str,
) -> ProviderUIContext:
    """Build the read-only UI context for a single provider."""
    models = config_manager.get_models(provider_name)
    return ProviderUIContext(
        provider_id=provider_name,
        models=models,
        default_model=models[0] if models else None,
        max_images=config_manager.get_max_images(provider_name),
        aspect_ratios=config_manager.get_aspect_ratios(provider_name),
        resolutions=config_manager.get_resolutions(provider_name),
        prompt_hint=config_manager.get_provider_hint(provider_name) or "",
    )


def build_ui_context(config_manager: ConfigManager) -> UIContext:
    """Build the read-only UI context used by the application shell."""
    ui_config = config_manager.get_ui_config()
    provider_names = config_manager.get_provider_names()
    providers = {
        provider_name: build_provider_context(config_manager, provider_name)
        for provider_name in provider_names
    }
    return UIContext(
        title=str(ui_config.get("title", "Sinyuk Imagen")),
        show_admin_tab=bool(ui_config.get("show_admin_tab", False)),
        active_provider=config_manager.get_active_provider_name(),
        providers=providers,
    )
