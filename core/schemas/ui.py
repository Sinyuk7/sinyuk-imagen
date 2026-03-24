"""UI-facing read models returned by the core facade."""

from dataclasses import dataclass, field

from core.schemas.ids import ModelDisplayName, ProviderId


@dataclass(frozen=True)
class ProviderUIContext:
    """Provider-specific options needed to render UI controls."""

    provider_id: ProviderId
    models: list[ModelDisplayName] = field(default_factory=list)
    default_model: ModelDisplayName | None = None
    max_images: int = 1
    aspect_ratios: list[str] = field(default_factory=list)
    resolutions: list[str] = field(default_factory=list)
    prompt_hint: str = ""


@dataclass(frozen=True)
class UIContext:
    """All read-only UI context needed to render and switch providers."""

    title: str = "Sinyuk Imagen"
    show_admin_tab: bool = False
    active_provider: ProviderId | None = None
    providers: dict[ProviderId, ProviderUIContext] = field(default_factory=dict)

    def get_provider(self, provider_id: ProviderId) -> ProviderUIContext:
        return self.providers[provider_id]
