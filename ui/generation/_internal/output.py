"""Output panel for the generation slice."""

from __future__ import annotations

import gradio as gr # pyright: ignore[reportMissingImports]

from ui.generation._internal.component_base import BaseComponent


class OutputPanel(BaseComponent):
    """Render current task detail at the top and task list at the bottom."""

    def __init__(self, *, show_admin_tab: bool = False) -> None:
        super().__init__("output")
        self._show_admin_tab = show_admin_tab

    def render(self) -> None:
        """Render gallery, compare slider, log console, and task selector."""
        with gr.Tabs() as tabs:
            self._components["tabs"] = tabs
            with gr.Tab("Gallery"):
                self._components["gallery"] = gr.Gallery(
                    label="Generated Images",
                    columns=2,
                    height="auto",
                    object_fit="contain",
                    format="png",
                )
            with gr.Tab("ImageCompare"):
                self._components["image_slider"] = gr.ImageSlider(
                    label="Before / After",
                    type="filepath",
                )
            if self._show_admin_tab:
                with gr.Tab("Admin"):
                    self._components["admin_metrics"] = gr.Markdown(
                        value="### Admin Metrics\nNo task metrics available.",
                    )

        if not self._show_admin_tab:
            self._components["admin_metrics"] = gr.Markdown(value="", visible=False)

        self._components["status_bar"] = gr.HTML(
            value="",
            elem_id="generation-status-bar",
        )
        self._components["mark_saved_button"] = gr.Button(
            value="Mark Saved",
            visible=False,
            variant="secondary",
            elem_id="mark-saved-button",
        )
        self._components["mark_all_saved_button"] = gr.Button(
            value="Mark All Saved",
            visible=False,
            variant="secondary",
            elem_id="mark-all-saved-button",
        )
        self._components["task_history_list"] = gr.HTML(
            value="",
            elem_id="task-history-list",
        )
        self._components["task_selection_bridge"] = gr.Textbox(
            value="",
            visible="hidden",
            container=False,
            elem_id="task-selection-bridge",
        )
        with gr.Accordion("Log Console", open=False):
            self._components["logcat_output"] = gr.Markdown(value="")

    def get_gallery(self) -> gr.Gallery:
        return self._components["gallery"]

    def get_status_bar(self) -> gr.HTML:
        return self._components["status_bar"]

    def get_logcat_output(self) -> gr.Markdown:
        return self._components["logcat_output"]

    def get_image_slider(self) -> gr.ImageSlider:
        return self._components["image_slider"]

    def get_task_history_list(self) -> gr.HTML:
        return self._components["task_history_list"]

    def get_task_selection_bridge(self) -> gr.Textbox:
        return self._components["task_selection_bridge"]

    def get_mark_saved_button(self) -> gr.Button:
        return self._components["mark_saved_button"]

    def get_mark_all_saved_button(self) -> gr.Button:
        return self._components["mark_all_saved_button"]

    def get_admin_metrics(self) -> gr.Markdown:
        return self._components["admin_metrics"]
