"""Tests for generation output presenter error details."""

from core.schemas import TaskErrorCode
from ui.generation._internal.presenter import OutputPresenter


def test_build_error_result_keeps_raw_error_in_log_details() -> None:
    view_model = OutputPresenter.build_error_result(
        error_message="401 Unauthorized: invalid api key",
        error_code=TaskErrorCode.PROVIDER_ERROR,
    )

    assert "Your API key looks invalid" in view_model.status_text
    assert "Technical Error" in view_model.logcat_markdown
    assert "401 Unauthorized: invalid api key" in view_model.logcat_markdown
