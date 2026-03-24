"""Shared view-model types for the generation output presenter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SliderValue = tuple[Any | None, Any | None] | None


@dataclass
class OutputViewModel:
    """UI-ready output state consumed by the output panel."""

    gallery_items: list[Any] = field(default_factory=list)
    status_text: str = ""
    logcat_markdown: str = ""
    slider_value: SliderValue = None
    slider_temp_paths: list[str] = field(default_factory=list)
