"""
core/generation/_internal/provider_gateway - Provider 网关

INTENT: 管理 Provider 实例缓存和请求构建
SIDE EFFECT: None (Provider 实例缓存在内存中)
"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from core.schemas import ProviderExecutionRequest, TaskConfig

if TYPE_CHECKING:
    from core.config import ConfigManager
    from core.generation._internal.provider_base import BaseImageProvider


class ProviderGateway:
    """
    Provider 网关

    INTENT: 管理 Provider 实例的创建、缓存和请求构建
    SIDE EFFECT: 内部维护 Provider 实例缓存
    """

    def __init__(self, config_manager: "ConfigManager") -> None:
        """
        初始化 Provider 网关

        INTENT: 创建网关实例并初始化缓存
        INPUT: config_manager - 配置管理器
        OUTPUT: ProviderGateway 实例
        SIDE EFFECT: None
        FAILURE: 无
        """
        self._config = config_manager
        self._providers: Dict[str, "BaseImageProvider"] = {}

    def build_provider_request(self, task_config: TaskConfig) -> ProviderExecutionRequest:
        """
        构建 Provider 执行请求

        INTENT: 将 TaskConfig 转换为 Provider 可执行的请求对象
        INPUT: task_config - 任务配置
        OUTPUT: ProviderExecutionRequest
        SIDE EFFECT: None
        FAILURE: 无
        """
        provider_config = self._config.get_provider(task_config.provider)
        api_key = self._resolve_api_key(task_config, provider_config)
        auth_source = self._resolve_auth_source(task_config)
        model_name = self._config.get_model_name(task_config.provider, task_config.model)
        return ProviderExecutionRequest(
            task=task_config,
            model_name=model_name,
            api_key=api_key,
            auth_source=auth_source,
        )

    def get_or_create_provider(self, provider_name: str) -> "BaseImageProvider":
        """
        获取或创建 Provider 实例

        INTENT: 从缓存获取或创建新的 Provider 实例
        INPUT: provider_name - Provider 名称
        OUTPUT: BaseImageProvider 实例
        SIDE EFFECT: 可能更新内部缓存
        FAILURE: 抛出 KeyError (Provider 未注册)
        """
        if provider_name not in self._providers:
            # 延迟导入避免循环依赖
            from core.generation._internal.provider_registry import create_provider
            provider_config = self._config.get_provider(provider_name)
            self._providers[provider_name] = create_provider(provider_config)
        return self._providers[provider_name]

    @staticmethod
    def _resolve_api_key(task_config: TaskConfig, provider_config: Dict[str, Any]) -> str:
        """
        解析 API Key

        INTENT: 优先使用 UI 覆盖的 token，否则使用配置文件的 key
        INPUT:
            - task_config: 任务配置
            - provider_config: Provider 配置
        OUTPUT: API Key 字符串
        SIDE EFFECT: None
        FAILURE: 无
        """
        ui_token_override = task_config.ui_token_override
        if ui_token_override and ui_token_override.strip():
            return ui_token_override.strip()
        return str(provider_config.get("api_key", ""))

    @staticmethod
    def _resolve_auth_source(task_config: TaskConfig) -> str:
        """
        解析认证来源

        INTENT: 确定 API Key 的来源是 UI 还是配置文件
        INPUT: task_config - 任务配置
        OUTPUT: "ui" 或 "config/env"
        SIDE EFFECT: None
        FAILURE: 无
        """
        ui_token_override = task_config.ui_token_override
        if ui_token_override and ui_token_override.strip():
            return "ui"
        return "config/env"
