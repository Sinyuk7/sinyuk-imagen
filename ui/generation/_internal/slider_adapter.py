"""Helpers that normalize generation output into slider- and gallery-friendly values."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any
import uuid

from core.schemas import GeneratedImageArtifact
from ui.generation._internal.view_model import SliderValue


def build_slider_value(
    before_image: Any | None,
    after_image: Any | None,
) -> SliderValue:
    """Build a renderable compare-slider value."""
    if before_image is None and after_image is None:
        return None
    if before_image is not None and after_image is None:
        return before_image, before_image
    if before_image is None and after_image is not None:
        return after_image, after_image
    return before_image, after_image


def coerce_gallery_item(image_value: Any) -> Any:
    """Normalize gallery items into Gradio-renderable values."""
    if isinstance(image_value, GeneratedImageArtifact):
        return image_value.presentation_path
    return image_value


def coerce_slider_image(image_value: Any) -> tuple[Any, list[str]]:
    """Normalize slider images into a filepath-friendly value."""
    if isinstance(image_value, GeneratedImageArtifact):
        return image_value.presentation_path, []

    try:
        from PIL import Image

        if isinstance(image_value, Image.Image):
            temp_dir = Path(tempfile.gettempdir()) / "sinyuk-imagen" / "ui-slider-images"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / f"{uuid.uuid4().hex}.png"
            image_value.save(temp_path, format="PNG")
            return str(temp_path), [str(temp_path)]
    except ImportError:
        pass

    return image_value, []
