"""Small state helpers for the top-level Gradio application."""

from __future__ import annotations

import uuid
from typing import cast

import gradio as gr # pyright: ignore[reportMissingImports]
from gradio.blocks import Block # pyright: ignore[reportMissingImports]

from core.schemas import UIContext
from ui.generation.contracts import GenerationUIComponents
from ui.state_machine import StateMachine


def get_effective_aspect_ratio(ratio: str, flip_checked: bool) -> str:
    """Return the aspect ratio actually used by generation and preprocessing."""
    if not flip_checked or ":" not in ratio:
        return ratio
    width, height = ratio.split(":")
    return f"{height}:{width}"


def build_session_state(
    ui_context: UIContext,
    generation_ui: GenerationUIComponents,
) -> StateMachine:
    """Create per-session state with the active provider preloaded."""
    state_machine = StateMachine()
    initial_provider = ui_context.active_provider or ""
    state_machine.context.current_provider = initial_provider
    provider_context = generation_ui.basic_params.get_provider_context(initial_provider)
    state_machine.context.set_prompt_hint(
        initial_provider,
        provider_context.prompt_hint or "",
    )
    return state_machine


def build_prepared_reference_state() -> gr.State:
    """Create the prepared-reference image state holder."""
    return gr.State(value=None)


def build_page_session_id_state() -> gr.State:
    """Create the transient page-session id state holder."""
    return gr.State(value=None)


def ensure_page_session_id(value: str | None | object) -> str:
    """Return the existing page session id or create a new transient one."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return uuid.uuid4().hex


def build_browser_task_state_block() -> Block:
    """Create the page-owned task selection state."""
    return cast(
        Block,
        gr.State(value={"task_ids": [], "selected_task_id": None}),
    )


def build_refresh_timer_block() -> Block:
    """Create the auto-refresh timer or a state placeholder when unavailable."""
    timer_factory = getattr(gr, "Timer", None)
    if timer_factory is None:
        return cast(Block, gr.State(value=None))
    return cast(Block, timer_factory(value=2.0, active=False))
