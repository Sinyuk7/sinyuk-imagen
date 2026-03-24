"""Generation-specific orchestration helpers for the top-level app shell."""

from __future__ import annotations

import gradio as gr
from gradio.blocks import Block

import core.api as core_api
from core.schemas import BrowserTaskState, BrowserTaskStateValue
from ui._app_state import get_effective_aspect_ratio
from ui.generation import OutputPresenter
from ui.generation.contracts import GenerationUIComponents
from ui.state_machine import StateMachine


def prepare_reference_preview(
    generation_ui: GenerationUIComponents,
    reference_image_path: str | None,
    divisible_by: int,
    ratio: str,
    flip_checked: bool,
    state_machine: StateMachine,
) -> tuple[object, str | None, object, StateMachine]:
    """Prepare the business-owned reference image and sync the compare slider."""
    ref_image_info = generation_ui.basic_params.validate_image_dimensions(
        reference_image_path,
        divisible_by,
    )
    final_ratio = get_effective_aspect_ratio(ratio, flip_checked)

    if reference_image_path is None:
        view_model = OutputPresenter.build_reference_preview(None)
        state_machine.context.replace_slider_temp_paths(view_model.slider_temp_paths)
        return ref_image_info, None, view_model.slider_value, state_machine

    try:
        prepared_reference = core_api.prepare_reference_image(
            raw_reference_image_path=reference_image_path,
            divisible_by=divisible_by,
            aspect_ratio=final_ratio,
        )
    except Exception as exc:
        gr.Warning(f"Failed to prepare reference image: {exc}")
        view_model = OutputPresenter.build_reference_preview(None)
        state_machine.context.replace_slider_temp_paths(view_model.slider_temp_paths)
        return ref_image_info, None, view_model.slider_value, state_machine

    prepared_path = (
        prepared_reference.prepared_path if prepared_reference is not None else None
    )
    view_model = OutputPresenter.build_reference_preview(prepared_path)
    state_machine.context.replace_slider_temp_paths(view_model.slider_temp_paths)
    return ref_image_info, prepared_path, view_model.slider_value, state_machine


def bind_generation_events(
    generation_ui: GenerationUIComponents,
    prepared_reference_state: gr.State,
    browser_task_state: Block,
    session_state_machine: gr.State,
    refresh_timer: Block,
) -> None:
    """Bind provider, reference-preview, and generate events."""
    basic_params = generation_ui.basic_params
    advanced_params = generation_ui.advanced_params
    output = generation_ui.output

    basic_params.get_component("provider").change(
        fn=lambda provider_name, current_token, state_machine: generation_ui.provider_handler.handle_provider_change(
            provider_name,
            current_token,
            state_machine,
        ).to_output_tuple(),
        inputs=[
            basic_params.get_component("provider"),
            advanced_params.get_component("provider_token"),
            session_state_machine,
        ],
        outputs=[
            basic_params.get_component("model"),
            basic_params.get_component("batch_count"),
            basic_params.get_component("aspect_ratio"),
            basic_params.get_component("resolution"),
            advanced_params.get_component("provider_token"),
            basic_params.get_component("prompt"),
            session_state_machine,
        ],
    )

    advanced_params.get_component("provider_token").change(
        fn=generation_ui.provider_handler.save_token,
        inputs=[
            basic_params.get_component("provider"),
            advanced_params.get_component("provider_token"),
            session_state_machine,
        ],
        outputs=[session_state_machine],
    )

    reference_preview_inputs = [
        basic_params.get_component("reference_image"),
        basic_params.get_component("divisible_by"),
        basic_params.get_component("aspect_ratio"),
        basic_params.get_component("flip_ratio"),
        session_state_machine,
    ]
    reference_preview_outputs = [
        basic_params.get_component("ref_image_info"),
        prepared_reference_state,
        output.get_image_slider(),
        session_state_machine,
    ]
    for input_name in (
        "reference_image",
        "divisible_by",
        "aspect_ratio",
        "flip_ratio",
    ):
        basic_params.get_component(input_name).change(
            fn=lambda reference_image_path, divisible_by, ratio, flip_checked, state_machine: prepare_reference_preview(
                generation_ui,
                reference_image_path,
                divisible_by,
                ratio,
                flip_checked,
                state_machine,
            ),
            inputs=reference_preview_inputs,
            outputs=reference_preview_outputs,
        )

    generation_ui.controls.get_button().click(
        fn=lambda prompt_text, provider_name, model_name, img_count, ratio, flip_checked, resolution, neg_prompt, seed_val, guidance_enabled, guidance_val, advanced_json, provider_token_val, debug_mode, reference_image_path, divisible_by, browser_state_value, state_machine: generation_ui.generate_handler.handle_generate(
            prompt_text,
            provider_name,
            model_name,
            img_count,
            ratio,
            flip_checked,
            resolution,
            neg_prompt,
            seed_val,
            guidance_enabled,
            guidance_val,
            advanced_json,
            provider_token_val,
            debug_mode,
            reference_image_path,
            divisible_by,
            browser_state_value,
            state_machine,
        ).to_output_tuple(),
        inputs=[
            basic_params.get_component("prompt"),
            basic_params.get_component("provider"),
            basic_params.get_component("model"),
            basic_params.get_component("batch_count"),
            basic_params.get_component("aspect_ratio"),
            basic_params.get_component("flip_ratio"),
            basic_params.get_component("resolution"),
            advanced_params.get_component("negative_prompt"),
            advanced_params.get_component("seed"),
            advanced_params.get_component("enable_guidance"),
            advanced_params.get_component("guidance_scale"),
            advanced_params.get_component("advanced_params"),
            advanced_params.get_component("provider_token"),
            advanced_params.get_component("debug_mode"),
            basic_params.get_component("reference_image"),
            basic_params.get_component("divisible_by"),
            browser_task_state,
            session_state_machine,
        ],
        outputs=[
            browser_task_state,
            output.get_current_task(),
            output.get_gallery(),
            output.get_status_bar(),
            output.get_logcat_output(),
            output.get_image_slider(),
            output.get_task_selector(),
            refresh_timer,
            output.get_admin_metrics(),
            session_state_machine,
        ],
        queue=False,
    )


def output_tuple_inputs(
    browser_state_value: BrowserTaskState | BrowserTaskStateValue | object,
) -> BrowserTaskState | BrowserTaskStateValue | object:
    """Tiny helper to keep Gradio callback lambdas readable."""
    return browser_state_value
