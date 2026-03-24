"""Generation output presenter facade built from smaller helper modules."""

from __future__ import annotations

from typing import Any

from core.schemas import GenerationResult, ProviderDiagnostics, TaskErrorCode, TaskSnapshot, TaskStatus
from ui.generation._internal.log_renderer import render_logcat
from ui.generation._internal.slider_adapter import (
    build_slider_value,
    coerce_gallery_item,
    coerce_slider_image,
)
from ui.generation._internal.status_formatter import build_error_status, build_success_status
from ui.generation._internal.view_model import OutputViewModel, SliderValue


class OutputPresenter:
    """Map domain-layer generation results into UI-ready output values."""

    @staticmethod
    def build_reference_preview(reference_image: Any | None) -> OutputViewModel:
        """Build the compare slider state for reference-image preview updates."""
        return OutputViewModel(
            slider_value=build_slider_value(
                before_image=reference_image,
                after_image=None,
            )
        )

    @staticmethod
    def build_empty_result() -> OutputViewModel:
        """Build the empty-state view model for task details."""
        return OutputViewModel(status_text="Select a task below to inspect its result.")

    @staticmethod
    def build_generation_success(result: GenerationResult) -> OutputViewModel:
        """Build a UI view model for a successful generation result."""
        elapsed = float(result.metadata.get("elapsed_seconds", 0))
        slider_after_image, temp_paths = (
            coerce_slider_image(result.images[0]) if result.images else (None, [])
        )
        return OutputViewModel(
            gallery_items=[coerce_gallery_item(image_value) for image_value in result.images],
            status_text=build_success_status(
                image_count=len(result.images),
                elapsed_seconds=elapsed,
                provider=result.provider,
                model=result.model,
                diagnostics=result.diagnostics,
            ),
            logcat_markdown=render_logcat(result=result, diagnostics=result.diagnostics),
            slider_value=build_slider_value(
                before_image=result.prepared_reference_image_path,
                after_image=slider_after_image,
            ),
            slider_temp_paths=temp_paths,
        )

    @staticmethod
    def build_debug_result(result: GenerationResult) -> OutputViewModel:
        """Build a UI view model for debug-mode output."""
        return OutputViewModel(
            status_text="Dry run only. Request not sent.",
            logcat_markdown=render_logcat(result=result, diagnostics=result.diagnostics),
        )

    @staticmethod
    def build_task_pending(snapshot: TaskSnapshot) -> OutputViewModel:
        """Build a pending/running task detail model."""
        status_line = {
            TaskStatus.QUEUED.value: "**Queued**  \nWaiting for an available worker.",
            TaskStatus.PREPARING.value: "**Preparing**  \nCopying inputs and normalizing task assets.",
            TaskStatus.RUNNING.value: "**Running**  \nImage generation is in progress.",
        }.get(snapshot.status.value, f"**{str(snapshot.status.value).title()}**")
        detail_line = f"`{snapshot.provider}` | `{snapshot.model}`"
        return OutputViewModel(
            status_text="  \n".join([status_line, detail_line]),
            slider_value=build_slider_value(
                before_image=snapshot.prepared_reference_image_path,
                after_image=None,
            ),
        )

    @staticmethod
    def build_error_result(
        error_message: str,
        error_code: TaskErrorCode | None = None,
        result: GenerationResult | None = None,
        diagnostics: ProviderDiagnostics | None = None,
    ) -> OutputViewModel:
        """Build a UI view model for an error state."""
        return OutputViewModel(
            status_text=build_error_status(
                error_message=error_message,
                error_code=error_code,
            ),
            logcat_markdown=render_logcat(result=result, diagnostics=diagnostics),
        )

    @staticmethod
    def render_logcat(
        result: GenerationResult | None = None,
        diagnostics: ProviderDiagnostics | None = None,
    ) -> str:
        """Render provider diagnostics into concise markdown for the UI panel."""
        return render_logcat(result=result, diagnostics=diagnostics)


__all__ = ["OutputPresenter", "OutputViewModel", "SliderValue"]
