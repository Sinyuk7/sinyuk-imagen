"""
core/generation/_internal - 私有实现模块

⚠️ 警告：此目录下的模块仅供 core/generation 内部使用。
禁止从其他 feature slice 导入此目录下的任何内容。
跨模块通信必须通过 core/generation/entry.py 的公开函数。

注意：为避免循环导入和依赖问题，所有导入应直接从子模块进行，
而不是从此 __init__.py 导入。
"""

# 定义公开 API，但不在模块级别导入
# 这些模块应直接导入使用：
#   from core.generation._internal.provider_base import BaseImageProvider
#   from core.generation._internal.provider_gateway import ProviderGateway
#   等等

__all__ = [
    "BaseImageProvider",
    "ProviderGateway",
    "ReferenceImagePreparer",
    "build_failure_result",
    "create_provider",
    "get_provider_types",
    "normalize_task_config",
    "validate_task_config",
]


def __getattr__(name: str):
    """延迟导入以避免循环依赖和不必要的依赖加载。"""
    if name == "BaseImageProvider":
        from core.generation._internal.provider_base import BaseImageProvider
        return BaseImageProvider
    if name == "ProviderGateway":
        from core.generation._internal.provider_gateway import ProviderGateway
        return ProviderGateway
    if name == "ReferenceImagePreparer":
        from core.generation._internal.reference_images import ReferenceImagePreparer
        return ReferenceImagePreparer
    if name in ("create_provider", "get_provider_types"):
        from core.generation._internal import provider_registry
        return getattr(provider_registry, name)
    if name in ("build_failure_result", "normalize_task_config", "validate_task_config"):
        from core.generation._internal import task_config
        return getattr(task_config, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")