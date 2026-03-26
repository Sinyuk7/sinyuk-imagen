"""Tests for human-readable generation status messages."""

from core.schemas import TaskErrorCode
from ui.generation._internal.status_formatter import (
    build_error_status,
    build_success_status,
    explain_error,
)


def test_explain_error_maps_invalid_api_key_into_plain_language() -> None:
    message = explain_error("401 Unauthorized: invalid api key", TaskErrorCode.PROVIDER_ERROR)
    assert "API key" in message
    assert "invalid" in message.lower()


def test_explain_error_maps_timeout_into_retryable_language() -> None:
    message = explain_error("provider request timed out", TaskErrorCode.TIMED_OUT)
    assert "too long" in message.lower()
    assert "try again" in message.lower()


def test_explain_error_maps_queue_full_into_user_action() -> None:
    message = explain_error("queue is full", TaskErrorCode.QUEUE_FULL)
    assert "too many image tasks" in message.lower()
    assert "try again" in message.lower()


def test_build_error_status_renders_error_card_markup() -> None:
    markup = build_error_status(
        "401 Unauthorized: invalid api key",
        TaskErrorCode.PROVIDER_ERROR,
    )
    assert "generation-status-card" in markup
    assert "status-error" in markup
    assert "API key" in markup


def test_build_success_status_renders_success_card_markup() -> None:
    markup = build_success_status(
        image_count=2,
        elapsed_seconds=12.34,
        provider="n1n.ai",
        model="Nano Banana 2",
    )
    assert "generation-status-card" in markup
    assert "status-success" in markup
    assert "2 image(s) ready" in markup
