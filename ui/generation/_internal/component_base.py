"""Shared UI component base for the generation slice."""

from __future__ import annotations

from typing import Any


class BaseComponent:
    """Common container for Gradio component instances."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._components: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self._name

    def render(self) -> None:
        """Render the component tree for this panel."""
        raise NotImplementedError("Subclass must implement render()")

    def get_component(self, key: str) -> Any:
        """Return a previously rendered child component."""
        if key not in self._components:
            raise KeyError(f"Component '{key}' not found in {self._name}")
        return self._components[key]
