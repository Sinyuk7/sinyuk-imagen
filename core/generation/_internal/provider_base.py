"""
core/generation/_internal/provider_base - Provider 基类

INTENT: 定义所有图像生成 Provider 的抽象基类
SIDE EFFECT: FILE_SYSTEM (生成图像持久化)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any

from core.generation._internal._provider_diagnostics import (
    append_fact,
    validate_requested_resolution,
)
from core.generation._internal._provider_materialization import (
    materialize_generated_image,
    sanitize_source_uri,
)
from core.schemas import (
    GeneratedImageArtifact,
    GenerationResult,
    ProviderDiagnosticFact,
    ProviderExecutionRequest,
    TaskConfig,
)


class BaseImageProvider(ABC):
    """
    图像生成 Provider 抽象基类

    INTENT: 定义 Provider 实现必须遵循的契约
    SIDE EFFECT: FILE_SYSTEM (通过 _materialize_generated_image)
    """

    def __init__(self, config: dict[str, Any]):
        """
        初始化 Provider

        INTENT: 从配置字典初始化 Provider 实例
        INPUT: config - Provider 配置字典，必须包含 name, base_url, api_key
        OUTPUT: Provider 实例
        SIDE EFFECT: None
        FAILURE: KeyError (缺少必要配置字段)
        """
        self._config = config
        self._name = config["name"]
        self._base_url = config["base_url"]
        self._api_key = config["api_key"]
        self._models = config.get("models", {})
        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    async def generate(self, request: ProviderExecutionRequest) -> GenerationResult:
        """
        执行图像生成

        INTENT: 异步执行一个准备好的 Provider 请求
        INPUT: request - Provider 执行请求
        OUTPUT: GenerationResult
        SIDE EFFECT: NETWORK (调用外部 API), FILE_SYSTEM (保存生成图像)
        FAILURE: 返回包含 error 的 GenerationResult
        """

    def get_supported_resolutions(self, model_name: str) -> list[str] | None:
        """
        获取支持的分辨率

        INTENT: 返回模型支持的分辨率令牌，用于验证
        INPUT: model_name - 模型名称
        OUTPUT: 分辨率列表或 None (未知)
        SIDE EFFECT: None
        FAILURE: 返回 None
        """
        return None

    def _append_fact(
        self,
        facts: list[ProviderDiagnosticFact],
        code,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """追加一个结构化诊断事实。"""
        append_fact(facts, code, payload)

    def _validate_requested_resolution(
        self,
        task_config: TaskConfig,
        model_name: str,
        facts: list[ProviderDiagnosticFact],
    ) -> str | None:
        """验证请求的分辨率是否被模型支持。"""
        return validate_requested_resolution(
            task_config=task_config,
            model_name=model_name,
            supported_resolutions=self.get_supported_resolutions(model_name),
            facts=facts,
        )

    def _materialize_generated_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str | None,
        model_name: str,
        requested_resolution: str | None,
        facts: list[ProviderDiagnosticFact],
        source_uri: str | None = None,
        source_kind: str = "inline_data",
    ) -> GeneratedImageArtifact:
        """持久化一个生成图像并返回丰富的 artifact。"""
        return materialize_generated_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            provider_name=self._name,
            model_name=model_name,
            requested_resolution=requested_resolution,
            facts=facts,
            source_uri=source_uri,
            source_kind=source_kind,
        )

    @staticmethod
    def _sanitize_source_uri(value: str) -> str:
        """从源 URI 中去除查询和片段。"""
        return sanitize_source_uri(value)

    def _log_provider_failure(self, elapsed_seconds: float, error_message: str) -> None:
        """发出一个通用 provider 失败日志条目。"""
        self._logger.error(
            "Provider '%s' failed after %.2fs: %s",
            self._name,
            elapsed_seconds,
            error_message,
        )
