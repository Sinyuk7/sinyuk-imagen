"""Fresh-interpreter import checks to catch circular-import regressions."""

from __future__ import annotations

import subprocess
import sys
from textwrap import dedent


def test_packages_import_cleanly_in_fresh_interpreter() -> None:
    """INTENT: 在全新解释器里验证 core/ui 导入链路没有循环依赖阻塞。"""
    script = dedent(
        """
        import importlib
        import pkgutil

        module_names = {"app"}
        for package_name in ("core", "ui"):
            package = importlib.import_module(package_name)
            module_names.add(package_name)
            if hasattr(package, "__path__"):
                for module_info in pkgutil.walk_packages(
                    package.__path__,
                    prefix=f"{package_name}.",
                ):
                    module_names.add(module_info.name)

        for module_name in sorted(module_names):
            importlib.import_module(module_name)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
