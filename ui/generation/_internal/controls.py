"""Control panel for the generation slice."""

from __future__ import annotations

import gradio as gr

from ui.generation._internal.component_base import BaseComponent


class ControlsPanel(BaseComponent):
    """Render action buttons for generation."""

    def __init__(self) -> None:
        super().__init__("controls")

    def render(self) -> None:
        """Render the generate button."""
        self._components["generate_btn"] = gr.Button(
            "🎨 Generate",
            variant="primary",
            size="lg",
            elem_id="generate-button",
        )

    def get_button(self) -> gr.Button:
        """Return the generate button."""
        return self._components["generate_btn"]
