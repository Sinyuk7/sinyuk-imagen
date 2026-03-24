"""Compatibility wrapper re-exporting the split generation UI component modules."""

from ui.generation._internal.advanced_params import AdvancedParamsPanel
from ui.generation._internal.basic_params import (
    BasicParamsPanel,
    DEFAULT_PROMPT_PLACEHOLDER,
)
from ui.generation._internal.component_base import BaseComponent
from ui.generation._internal.controls import ControlsPanel
from ui.generation._internal.output import OutputPanel

__all__ = [
    "AdvancedParamsPanel",
    "BaseComponent",
    "BasicParamsPanel",
    "ControlsPanel",
    "DEFAULT_PROMPT_PLACEHOLDER",
    "OutputPanel",
]
