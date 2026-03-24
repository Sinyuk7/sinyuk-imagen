"""
core/generation/contracts - 图像生成模块的公开类型契约

INTENT:
    定义 generation 模块与外部交互的所有类型契约。
    这些类型是稳定的公开 API，修改需要考虑向后兼容。

SIDE EFFECT: None (纯类型定义)
"""

from dataclasses import dataclass, field
from typing import TypeAlias

GenerationParams: TypeAlias = dict[str, object]
GenerationMetadata: TypeAlias = dict[str, object]


@dataclass(frozen=True)
class ReferenceImageSpec:
    """
    参考图像规格

    INTENT: 描述用于图像生成的参考图像配置
    """

    source_path: str
    divisible_by: int = 1
    aspect_ratio: str | None = None


@dataclass(frozen=True)
class GenerationRequest:
    """
    图像生成请求

    INTENT: 封装单次图像生成所需的全部参数
    INPUT: 由 UI 层或 API 层构造
    """

    provider_id: str
    model_id: str
    prompt: str
    negative_prompt: str = ""
    image_count: int = 1
    aspect_ratio: str | None = None
    resolution: str | None = None
    reference_image: ReferenceImageSpec | None = None
    params: GenerationParams = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.image_count < 1:
            object.__setattr__(self, "image_count", 1)
        if not self.prompt.strip():
            raise ValueError("prompt cannot be empty")


@dataclass(frozen=True)
class GeneratedImage:
    """
    生成的单张图像

    INTENT: 描述生成结果中的单张图像及其元数据
    """

    path: str
    width: int
    height: int
    mime_type: str = "image/png"
    download_name: str | None = None
    content_hash: str | None = None


@dataclass
class GenerationResponse:
    """
    图像生成响应

    INTENT: 封装图像生成的完整结果
    OUTPUT: 由 generation 模块返回给调用方
    """

    images: list[GeneratedImage] = field(default_factory=list)
    success: bool = False
    error_code: str | None = None
    error_message: str | None = None
    metadata: GenerationMetadata = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.success and len(self.images) > 0

    @property
    def is_failure(self) -> bool:
        return not self.success
