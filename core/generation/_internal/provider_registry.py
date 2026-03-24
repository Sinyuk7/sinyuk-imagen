"""
core/generation/_internal/provider_registry - Provider 显式注册表

INTENT: 提供显式的 Provider 注册和工厂功能
SIDE EFFECT: None

说明：
    所有 Provider 类型必须在此文件中显式列出。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from core.generation._internal.provider_base import BaseImageProvider

logger = logging.getLogger(__name__)


def _get_provider_registry() -> Dict[str, Type["BaseImageProvider"]]:
    """
    获取 Provider 注册表

    INTENT: 延迟导入并构建 Provider 类型映射
    INPUT: None
    OUTPUT: provider_type -> provider_class 的映射
    SIDE EFFECT: None
    FAILURE: 无
    """
    from core.generation._internal.providers.google import GoogleCompatibleProvider

    return {
        "google_compatible": GoogleCompatibleProvider,
    }


def get_provider_types() -> list[str]:
    """
    获取所有注册的 Provider 类型

    INTENT: 返回可用的 Provider 类型列表
    INPUT: None
    OUTPUT: Provider 类型名称列表
    SIDE EFFECT: None
    FAILURE: 无
    """
    return list(_get_provider_registry().keys())


def create_provider(provider_config: Dict[str, Any]) -> "BaseImageProvider":
    """
    创建 Provider 实例

    INTENT: 根据配置字典创建 Provider 实例
    INPUT: provider_config - Provider 配置字典，必须包含 'type' 字段
    OUTPUT: BaseImageProvider 实例
    SIDE EFFECT: None
    FAILURE: 抛出 KeyError (Provider 类型未注册)
    """
    provider_type = provider_config.get("type", "")
    registry = _get_provider_registry()

    if provider_type not in registry:
        available = list(registry.keys())
        raise KeyError(
            f"Provider type '{provider_type}' is not registered. "
            f"Available types: {available}"
        )

    cls = registry[provider_type]
    logger.info(
        "Creating provider '%s' (type=%s, class=%s)",
        provider_config.get("name", "unknown"),
        provider_type,
        cls.__name__,
    )
    return cls(provider_config)