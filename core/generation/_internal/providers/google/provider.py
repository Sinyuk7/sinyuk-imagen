"""Google-compatible async image generation provider."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.generation._internal.provider_base import BaseImageProvider
from core.generation._internal.providers.google._client import build_async_client, generate_content
from core.generation._internal.providers.google._request_builder import (
    build_api_contents,
    build_content_config,
)
from core.generation._internal.providers.google._response_parser import extract_images
from core.generation._internal.providers.google.diagnostics import build_debug_diagnostic_facts
from core.schemas import (
    DiagnosticCode,
    GenerationResult,
    ProviderDiagnosticFact,
    ProviderDiagnostics,
    ProviderExecutionRequest,
)

_DEFAULT_API_VERSION = "v1alpha"
_MODEL_SUPPORTED_RESOLUTIONS: Dict[str, List[str]] = {
    "gemini-2.5-flash-image": ["1K"],
    "gemini-3.1-flash-image-preview": ["0.5K", "1K", "2K", "4K"],
    "gemini-3-pro-image-preview": ["1K", "2K", "4K"],
}


class GoogleCompatibleProvider(BaseImageProvider):
    """
    Google-compatible 图像生成 Provider

    INTENT: 通过 Google-compatible API 生成图像
    SIDE EFFECT: NETWORK (调用外部 API), FILE_SYSTEM (保存生成图像)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._api_version = str(config.get("api_version", _DEFAULT_API_VERSION))

    def get_supported_resolutions(self, model_name: str) -> Optional[List[str]]:
        """Return known resolution capabilities for Google-compatible models."""
        return list(_MODEL_SUPPORTED_RESOLUTIONS.get(model_name, [])) or None

    async def generate(self, request: ProviderExecutionRequest) -> GenerationResult:
        """Generate images via the async Google-compatible SDK client."""
        start_time = time.time()
        facts: List[ProviderDiagnosticFact] = []
        request_sent = False
        task_config = request.task

        try:
            self._append_fact(
                facts,
                DiagnosticCode.RESOLVED_MODEL,
                {
                    "model_display_name": task_config.model,
                    "model_name": request.model_name,
                },
            )

            content_config = build_content_config(task_config)
            supported_resolutions = self.get_supported_resolutions(request.model_name)
            self._append_fact(
                facts,
                DiagnosticCode.REQUEST_CONFIGURED,
                {
                    "resolution": task_config.params.get("resolution"),
                    "aspect_ratio": task_config.params.get("aspect_ratio"),
                    "has_reference_image": bool(task_config.prepared_reference_image_path),
                    "supported_resolutions": supported_resolutions or [],
                },
            )
            validation_error = self._validate_requested_resolution(
                task_config=task_config,
                model_name=request.model_name,
                facts=facts,
            )
            if validation_error:
                elapsed = time.time() - start_time
                return self._build_result(
                    task_config=task_config,
                    facts=facts,
                    elapsed=elapsed,
                    error=validation_error,
                    success=False,
                )

            if task_config.debug_mode:
                facts.extend(
                    build_debug_diagnostic_facts(
                        provider_name=self._name,
                        base_url=self._base_url,
                        api_version=self._api_version,
                        model_display_name=task_config.model,
                        model_name=request.model_name,
                        prompt=task_config.prompt,
                        auth_source=request.auth_source,
                        content_config=content_config,
                    )
                )
                elapsed = time.time() - start_time
                return self._build_result(
                    task_config=task_config,
                    facts=facts,
                    elapsed=elapsed,
                    metadata={"debug_mode": True, "elapsed_seconds": round(elapsed, 2)},
                    success=True,
                )

            client = build_async_client(
                api_key=request.api_key,
                api_version=self._api_version,
                base_url=self._base_url,
            )
            self._append_fact(
                facts,
                DiagnosticCode.CLIENT_INITIALIZED,
                {
                    "base_url": self._base_url,
                    "api_version": self._api_version,
                    "auth_source": request.auth_source,
                },
            )

            api_contents = build_api_contents(
                task_config,
                facts,
                append_fact=self._append_fact,
            )
            self._append_fact(
                facts,
                DiagnosticCode.REQUEST_DISPATCHED,
                {
                    "request_sent": True,
                    "has_reference_image": bool(task_config.prepared_reference_image_path),
                },
            )

            request_sent = True
            response = await generate_content(
                client,
                model=request.model_name,
                contents=api_contents,
                config=content_config,
            )
            images = extract_images(
                response,
                model_name=request.model_name,
                requested_resolution=task_config.params.get("resolution"),
                facts=facts,
                append_fact=self._append_fact,
                materialize_generated_image=self._materialize_generated_image,
                sanitize_source_uri=self._sanitize_source_uri,
            )
            elapsed = time.time() - start_time
            self._append_fact(
                facts,
                DiagnosticCode.RESPONSE_RECEIVED,
                {
                    "image_count": len(images),
                    "elapsed_seconds": round(elapsed, 2),
                    "request_sent": request_sent,
                },
            )
            return self._build_result(
                task_config=task_config,
                facts=facts,
                elapsed=elapsed,
                images=images,
                success=True,
            )
        except Exception as exc:
            elapsed = time.time() - start_time
            error_msg = f"API error ({self._name}): {type(exc).__name__}: {exc}"
            self._log_provider_failure(elapsed, error_msg)
            self._append_fact(
                facts,
                DiagnosticCode.PROVIDER_ERROR,
                {
                    "error": error_msg,
                    "elapsed_seconds": round(elapsed, 2),
                    "request_sent": request_sent,
                },
            )
            return self._build_result(
                task_config=task_config,
                facts=facts,
                elapsed=elapsed,
                error=error_msg,
                success=False,
            )

    def _build_result(
        self,
        *,
        task_config,
        facts: List[ProviderDiagnosticFact],
        elapsed: float,
        images: list[Any] | None = None,
        metadata: Dict[str, Any] | None = None,
        error: str | None = None,
        success: bool,
    ) -> GenerationResult:
        return GenerationResult(
            images=[] if images is None else images,
            provider=self._name,
            model=task_config.model,
            metadata={"elapsed_seconds": round(elapsed, 2)} if metadata is None else metadata,
            diagnostics=ProviderDiagnostics(facts=facts),
            prepared_reference_image_path=task_config.prepared_reference_image_path,
            error=error,
            success=success,
        )