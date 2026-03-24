"""Private request-building helpers for the Google-compatible provider."""

from __future__ import annotations

import os
from typing import Any

from PIL import Image
from google.genai import types

from core.schemas import DiagnosticCode, ProviderDiagnosticFact, TaskConfig


def build_content_config(task_config: TaskConfig) -> Any:
    """Translate generic task params into the SDK request config."""
    config_kwargs: dict[str, Any] = {"response_modalities": ["IMAGE"]}

    resolution = task_config.params.get("resolution")
    if not resolution:
        raise ValueError(
            "Missing required parameter: 'resolution'. Must be provided (e.g., '1K', '2K', '4K')."
        )

    aspect_ratio = task_config.params.get("aspect_ratio")
    image_kwargs: dict[str, Any] = {"image_size": str(resolution).upper()}
    if aspect_ratio and aspect_ratio != "original":
        image_kwargs["aspect_ratio"] = aspect_ratio
    config_kwargs["image_config"] = types.ImageConfig(**image_kwargs)

    safety_level_str = task_config.extra.get("safety_filter_level", "BLOCK_NONE")
    threshold_enum = getattr(
        types.HarmBlockThreshold,
        safety_level_str,
        types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    )
    config_kwargs["safety_settings"] = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=threshold_enum,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=threshold_enum,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=threshold_enum,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=threshold_enum,
        ),
    ]

    return types.GenerateContentConfig(**config_kwargs)


def build_api_contents(
    task_config: TaskConfig,
    facts: list[ProviderDiagnosticFact],
    *,
    append_fact,
) -> list[Any]:
    """Build the multimodal request contents from the prepared task."""
    api_contents: list[Any] = []
    prepared_reference_image_path = task_config.prepared_reference_image_path
    if prepared_reference_image_path:
        if not os.path.exists(prepared_reference_image_path):
            raise FileNotFoundError(
                "Prepared reference image not found at: "
                f"{prepared_reference_image_path}"
            )

        try:
            with Image.open(prepared_reference_image_path) as opened_image:
                ref_image = (
                    opened_image.convert("RGB")
                    if opened_image.mode == "RGBA"
                    else opened_image.copy()
                )
            api_contents.append(ref_image)
            append_fact(
                facts,
                DiagnosticCode.REFERENCE_IMAGE_LOADED,
                {
                    "reference_image_path": prepared_reference_image_path,
                    "raw_reference_image_path": task_config.reference_image_path,
                },
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to process reference image: {exc}") from exc

    api_contents.append(task_config.prompt)
    return api_contents
