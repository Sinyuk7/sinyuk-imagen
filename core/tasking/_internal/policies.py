"""Private task orchestration policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class SupportsProviderConcurrencyConfig(Protocol):
    """Typed subset of ConfigManager used by the concurrency policy."""

    def get_provider_names(self) -> list[str]:
        ...

    def get_provider_max_concurrency(self, provider_name: str) -> int | None:
        ...


@dataclass(frozen=True)
class ProviderConcurrencyPolicy:
    """Strongly-typed provider concurrency limits for the runtime."""

    limits: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_config_manager(
        cls,
        config_manager: SupportsProviderConcurrencyConfig | None,
    ) -> "ProviderConcurrencyPolicy":
        if config_manager is None:
            return cls()

        limits: dict[str, int] = {}
        for provider_name in config_manager.get_provider_names():
            limit = config_manager.get_provider_max_concurrency(provider_name)
            if limit is None:
                continue
            normalized_limit = int(limit)
            if normalized_limit > 0:
                limits[provider_name] = normalized_limit
        return cls(limits=limits)

    def get_limit(self, provider_name: str) -> int | None:
        return self.limits.get(provider_name)
