"""
core/generation/entry - 图像生成模块入口

INTENT:
    提供图像生成功能的公开入口函数。
    这些函数是外部调用 generation 模块的唯一合法路径。

SIDE EFFECT: NETWORK | FILE_SYSTEM (通过内部实现)
"""

from __future__ import annotations

from dataclasses import replace
import logging
from typing import TYPE_CHECKING

from core.generation.contracts import (
    GeneratedImage,
    GenerationRequest,
    GenerationResponse,
)
from core.schemas import (
    GenerationResult,
    PreparedReferenceImage,
    TaskConfig,
)

if TYPE_CHECKING:
    from core.config import ConfigManager
    from core.generation._internal.provider_base import BaseImageProvider

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """
    图像生成服务

    INTENT: 提供图像生成的完整编排能力
    SIDE EFFECT: NETWORK | FILE_SYSTEM
    """

    def __init__(self, config_manager: "ConfigManager"):
        """
        初始化图像生成服务

        INTENT: 创建服务实例并初始化内部组件
        INPUT: config_manager - 配置管理器
        OUTPUT: ImageGenerationService 实例
        SIDE EFFECT: None
        FAILURE: 无
        """
        from core.generation._internal.provider_gateway import ProviderGateway
        from core.generation._internal.reference_images import ReferenceImagePreparer

        self._config = config_manager
        self._gateway = ProviderGateway(config_manager)
        self._reference_preparer = ReferenceImagePreparer()
        logger.info("ImageGenerationService initialized")

    async def generate(self, task_config: TaskConfig) -> GenerationResult:
        """
        执行图像生成

        INTENT: 根据 TaskConfig 调用 Provider 生成图像
        INPUT: task_config - 任务配置
        OUTPUT: GenerationResult - 生成结果
        SIDE EFFECT: NETWORK (调用外部 API), FILE_SYSTEM (保存生成图像)
        FAILURE: 返回带 error 的 GenerationResult
        """
        from core.generation._internal.task_config import (
            build_failure_result,
            normalize_task_config,
            validate_task_config,
        )

        try:
            normalized_task_config = normalize_task_config(task_config)
        except ValueError as exc:
            return build_failure_result(
                task_config,
                str(exc),
                prepared_reference_image_path=task_config.prepared_reference_image_path,
            )

        validation_error = validate_task_config(normalized_task_config, self._config)
        if validation_error:
            return build_failure_result(
                normalized_task_config,
                validation_error,
                prepared_reference_image_path=normalized_task_config.prepared_reference_image_path,
            )

        prepared_reference_image_path = normalized_task_config.prepared_reference_image_path
        try:
            if prepared_reference_image_path is None:
                prepared_reference = self.prepare_reference_image(
                    normalized_task_config.reference_image_path,
                    normalized_task_config.divisible_by,
                    normalized_task_config.params.get("aspect_ratio"),
                )
                prepared_reference_image_path = (
                    prepared_reference.prepared_path
                    if prepared_reference is not None
                    else prepared_reference_image_path
                )

            prepared_task_config = replace(
                normalized_task_config,
                prepared_reference_image_path=prepared_reference_image_path,
            )
            provider = self._gateway.get_or_create_provider(normalized_task_config.provider)
            provider_request = self._gateway.build_provider_request(prepared_task_config)
            result = await provider.generate(provider_request)
            if result.prepared_reference_image_path is None:
                result.prepared_reference_image_path = prepared_reference_image_path
            return result
        except Exception as exc:
            error_msg = f"Unexpected error: {type(exc).__name__}: {exc}"
            logger.exception(
                "ImageGenerationService caught unhandled exception for provider '%s'",
                normalized_task_config.provider,
            )
            return build_failure_result(
                normalized_task_config,
                error_msg,
                prepared_reference_image_path=prepared_reference_image_path,
            )

    def prepare_reference_image(
        self,
        raw_reference_image_path: str | None,
        divisible_by: int,
        aspect_ratio: str | None,
    ) -> PreparedReferenceImage | None:
        """
        准备参考图像

        INTENT: 预处理参考图像以适配 Provider 要求
        INPUT:
            - raw_reference_image_path: 原始图像路径
            - divisible_by: 尺寸整除值
            - aspect_ratio: 目标宽高比
        OUTPUT: PreparedReferenceImage 或 None
        SIDE EFFECT: FILE_SYSTEM (可能创建缓存文件)
        FAILURE: 抛出 FileNotFoundError
        """
        return self._reference_preparer.prepare(
            raw_reference_image_path,
            divisible_by,
            aspect_ratio,
        )


async def generate_image(request: GenerationRequest) -> GenerationResponse:
    """
    执行图像生成

    INTENT: 根据请求配置调用 Provider 生成图像
    INPUT: GenerationRequest - 完整的生成请求参数
    OUTPUT: GenerationResponse - 生成结果，包含图像列表或错误信息
    SIDE EFFECT: NETWORK (调用外部 API), FILE_SYSTEM (保存生成图像)
    FAILURE: 返回带 error_code 和 error_message 的 GenerationResponse
    """
    from core.config import ConfigManager

    params = dict(request.params)
    params["image_count"] = request.image_count
    if request.aspect_ratio:
        params["aspect_ratio"] = request.aspect_ratio
    if request.resolution:
        params["resolution"] = request.resolution
    if request.negative_prompt:
        params["negative_prompt"] = request.negative_prompt

    task_config = TaskConfig(
        prompt=request.prompt,
        provider=request.provider_id,
        model=request.model_id,
        params=params,
        reference_image_path=request.reference_image.source_path if request.reference_image else None,
        divisible_by=request.reference_image.divisible_by if request.reference_image else 1,
    )

    config_manager = ConfigManager()
    service = ImageGenerationService(config_manager)
    result = await service.generate(task_config)

    images: list[GeneratedImage] = []
    for artifact in result.images:
        images.append(
            GeneratedImage(
                path=artifact.presentation_path,
                width=artifact.width,
                height=artifact.height,
                mime_type=artifact.mime_type or "image/png",
                download_name=artifact.download_name,
                content_hash=artifact.content_hash,
            )
        )

    return GenerationResponse(
        images=images,
        success=result.success,
        error_code=None if result.success else "GENERATION_FAILED",
        error_message=result.error,
        metadata=result.metadata or {},
    )


def prepare_reference(
    source_path: str,
    divisible_by: int = 1,
    aspect_ratio: str | None = None,
) -> PreparedReferenceImage:
    """
    准备参考图像

    INTENT: 预处理参考图像
    INPUT:
        - source_path: 原始图像路径
        - divisible_by: 尺寸整除值
        - aspect_ratio: 目标宽高比
    OUTPUT: PreparedReferenceImage - 处理后的参考图像信息
    SIDE EFFECT: FILE_SYSTEM (可能需要转换或缓存图像)
    FAILURE: 抛出 ValueError (无效路径) 或 FileNotFoundError
    """
    from core.generation._internal.reference_images import ReferenceImagePreparer

    preparer = ReferenceImagePreparer()
    result = preparer.prepare(source_path, divisible_by=divisible_by, aspect_ratio=aspect_ratio)
    if result is None:
        raise ValueError(f"Failed to prepare reference image: {source_path}")
    return result


def get_provider_registry() -> dict[str, type["BaseImageProvider"]]:
    """
    获取 Provider 注册表

    INTENT: 返回所有已注册的 Provider 类型映射
    INPUT: None
    OUTPUT: dict[str, type[BaseImageProvider]] - provider_type -> provider_class 的映射
    SIDE EFFECT: None
    FAILURE: 返回空字典 (无注册 Provider)
    """
    from core.generation._internal.provider_registry import _get_provider_registry

    return _get_provider_registry()


def get_provider_types() -> list[str]:
    """
    获取所有注册的 Provider 类型

    INTENT: 返回可用的 Provider 类型名称列表
    INPUT: None
    OUTPUT: Provider 类型名称列表
    SIDE EFFECT: None
    FAILURE: 返回空列表
    """
    from core.generation._internal.provider_registry import get_provider_types as _get_types

    return _get_types()
