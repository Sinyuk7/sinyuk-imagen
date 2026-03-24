"""Diagnostics helpers for the Google-compatible provider."""

from typing import Any, List

from core.schemas import DiagnosticCode, ProviderDiagnosticFact


def build_debug_diagnostic_facts(
    *,
    provider_name: str,
    base_url: str,
    api_version: str,
    model_display_name: str,
    model_name: str,
    prompt: str,
    auth_source: str,
    content_config: Any,
) -> List[ProviderDiagnosticFact]:
    """Build structured debug-only facts from the exact request payload."""
    exact_payload = content_config.model_dump(by_alias=True, exclude_none=True)
    payload_with_contents = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        **exact_payload,
    }

    return [
        ProviderDiagnosticFact(
            code=DiagnosticCode.REQUEST_NOT_SENT,
            payload={
                "reason": "debug_mode",
                "request_sent": False,
            },
        ),
        ProviderDiagnosticFact(
            code=DiagnosticCode.REQUEST_SNAPSHOT,
            payload={
                "method": "POST",
                "url": (
                    f"{base_url.rstrip('/')}/{api_version}/models/"
                    f"{model_name}:generateContent"
                ),
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer ***",
                },
                "body": payload_with_contents,
                "_meta": {
                    "provider": provider_name,
                    "model_display_name": model_display_name,
                    "model_name": model_name,
                    "auth_source": auth_source,
                },
            },
        ),
    ]
