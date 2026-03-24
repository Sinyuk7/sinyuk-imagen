"""
core/generation - 图像生成核心业务模块

INTENT:
    提供图像生成的核心业务逻辑，包括任务配置、Provider 调度、结果处理。
    这是 generation feature slice 的公开入口。

PUBLIC API:
    - ImageGenerationService: 图像生成服务类
    - generate_image: 执行图像生成
    - prepare_reference: 准备参考图像
    - get_provider_registry: 获取 Provider 注册表
    - get_provider_types: 获取可用 Provider 类型

INTERNAL:
    - _internal/: 私有实现，禁止跨 feature 导入
"""

from core.generation.contracts import (
    GeneratedImage,
    GenerationRequest,
    GenerationResponse,
    ReferenceImageSpec,
)
from core.generation.entry import (
    ImageGenerationService,
    generate_image,
    get_provider_registry,
    get_provider_types,
    prepare_reference,
)

__all__ = [
    # 契约类型
    "GeneratedImage",
    "GenerationRequest",
    "GenerationResponse",
    "ReferenceImageSpec",
    # 服务类
    "ImageGenerationService",
    # 入口函数
    "generate_image",
    "get_provider_registry",
    "get_provider_types",
    "prepare_reference",
]