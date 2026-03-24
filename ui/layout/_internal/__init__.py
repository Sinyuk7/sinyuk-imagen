"""
ui/layout/_internal - Layout UI 内部实现

此目录包含 ui/layout 模块的内部实现细节。
外部模块不应直接导入此目录下的任何内容。
"""

from ui.layout._internal.footer import FooterPanel, FOOTER_CSS

__all__ = [
    "FooterPanel",
    "FOOTER_CSS",
]