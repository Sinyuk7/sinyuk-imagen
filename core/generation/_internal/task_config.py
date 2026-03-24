"""
core/generation/_internal/task_config - 任务配置规范化与验证

INTENT: 提供 TaskConfig 的规范化处理和验证功能
SIDE EFFECT: None
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, TYPE_CHECKING

from core.schemas import GenerationResult, TaskConfig

if TYPE_CHECKING:
    from core.config import ConfigManager


def normalize_task_config(task_config: TaskConfig) -> TaskConfig:
    """
    规范化任务配置

    INTENT: 返回经过规范化处理的 TaskConfig 副本
    INPUT: task_config - 原始任务配置
    OUTPUT: 规范化后的 TaskConfig
    SIDE EFFECT: None
    FAILURE: 抛出 ValueError (字段值无法转换)
    """
    return replace(
        task_config,
        params=_normalize_params(task_config.params),
        ui_token_override=_normalize_optional_string(task_config.ui_token_override),
        reference_image_path=_normalize_optional_string(task_config.reference_image_path),
        divisible_by=_normalize_int(task_config.divisible_by, field_name="divisible_by"),
    )


def validate_task_config(task_config: TaskConfig, config_manager: "ConfigManager") -> str | None:
    """
    验证任务配置

    INTENT: 验证规范化后的 TaskConfig 是否满足配置约束
    INPUT:
        - task_config: 规范化后的任务配置
        - config_manager: 配置管理器
    OUTPUT: 验证错误消息或 None (验证通过)
    SIDE EFFECT: None
    FAILURE: 返回错误消息字符串
    """
    if not task_config.prompt or not task_config.prompt.strip():
        return "Prompt must not be empty"

    provider_names = config_manager.get_provider_names()
    if task_config.provider not in provider_names:
        return (
            f"Provider '{task_config.provider}' not found. "
            f"Available: {provider_names}"
        )

    models = config_manager.get_models(task_config.provider)
    if task_config.model not in models:
        return (
            f"Model '{task_config.model}' is not available for provider "
            f"'{task_config.provider}'. Available models: {models}"
        )

    return None


def build_failure_result(
    task_config: TaskConfig,
    error_message: str,
    *,
    prepared_reference_image_path: str | None,
) -> GenerationResult:
    """
    构建失败结果

    INTENT: 构建稳定的失败响应，不向上层泄露异常
    INPUT:
        - task_config: 任务配置
        - error_message: 错误消息
        - prepared_reference_image_path: 已处理的参考图像路径
    OUTPUT: GenerationResult (success=False)
    SIDE EFFECT: None
    FAILURE: 无
    """
    return GenerationResult(
        images=[],
        provider=task_config.provider,
        model=task_config.model,
        prepared_reference_image_path=prepared_reference_image_path,
        error=error_message,
        success=False,
    )


def _normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """规范化参数字典，移除空值。"""
    normalized: Dict[str, Any] = {}
    for key, value in params.items():
        normalized_value = _normalize_param_value(key, value)
        if _should_keep_param_value(normalized_value):
            normalized[key] = normalized_value
    return normalized


def _normalize_param_value(key: str, value: Any) -> Any:
    """根据参数名称规范化参数值。"""
    if key == "image_count":
        return _normalize_int(value, field_name=key)
    if key == "seed":
        if value is None:
            return None
        return _normalize_int(value, field_name=key)
    if key == "guidance_scale":
        if value is None:
            return None
        return _normalize_float(value, field_name=key)
    if key == "resolution":
        normalized_text = _normalize_optional_string(value)
        return normalized_text.upper() if normalized_text else None
    if key in {"aspect_ratio", "negative_prompt"}:
        return _normalize_optional_string(value)
    if isinstance(value, str):
        return value.strip()
    return value


def _should_keep_param_value(value: Any) -> bool:
    """判断参数值是否应该保留。"""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    return True


def _normalize_optional_string(value: Any) -> str | None:
    """规范化可选字符串，空字符串转为 None。"""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_int(value: Any, *, field_name: str) -> int:
    """规范化整数值。"""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Parameter '{field_name}' must be an integer, got: {value!r}"
        ) from exc


def _normalize_float(value: Any, *, field_name: str) -> float:
    """规范化浮点数值。"""
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Parameter '{field_name}' must be a number, got: {value!r}"
        ) from exc
