"""Smoke tests for module importability after the feature-slice refactor."""

from __future__ import annotations

import importlib
import pkgutil


def _iter_module_names(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    module_names = [package_name]
    if hasattr(package, "__path__"):
        module_names.extend(
            module_info.name
            for module_info in pkgutil.walk_packages(
                package.__path__,
                prefix=f"{package_name}.",
            )
        )
    return module_names


MODULE_NAMES = sorted(
    {
        "app",
        * _iter_module_names("core"),
        * _iter_module_names("ui"),
    }
)


def test_all_modules_are_importable() -> None:
    """INTENT: 验证重构后的核心与 UI 模块都可以被导入。"""
    for module_name in MODULE_NAMES:
        importlib.import_module(module_name)
