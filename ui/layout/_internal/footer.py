"""
ui/layout/_internal/footer - Footer 面板组件

INTENT:
    提供应用底部的页脚面板，包含项目链接、版本信息等。

SIDE EFFECT: None (纯 UI 构建)
"""

from __future__ import annotations

from typing import Any, Dict

import gradio as gr


WECHAT_QR_URL = "https://github.com/Sinyuk7/sinyuk-imagen/blob/f5bb3e3d48c9d08e5a2d22ca1d61bc32539afd2f/asset/IMG_8101.JPG?raw=true"


FOOTER_CSS = """
/* =========================
   Design Tokens（你要的"可调参数"）
========================= */
:root {
    --badge-bg: rgba(0,0,0,0.04);
    --badge-bg-hover: rgba(0,0,0,0.08);

    --badge-text: #374151;

    --badge-padding-y: 6px;
    --badge-padding-x: 12px;

    --badge-radius: 999px;
    --badge-font-size: 12px;

    --badge-gap: 6px;

    --badge-shadow:
        0 1px 2px rgba(0,0,0,0.06),
        inset 0 1px 0 rgba(255,255,255,0.6);

    --glass-bg: rgba(255,255,255,0.7);
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
    :root {
        --badge-bg: rgba(255,255,255,0.08);
        --badge-bg-hover: rgba(255,255,255,0.12);
        --badge-text: #e5e7eb;

        --glass-bg: rgba(30,30,30,0.6);
    }
}

/* =========================
   Footer
========================= */
.footer {
    text-align: center;
    margin-top: 80px;
    padding: 30px 16px;
    border-top: 1px solid rgba(0,0,0,0.08);
}

.footer-row {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

/* =========================
   Inline Badge（核心）
========================= */
.inline-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--badge-gap);

    padding: var(--badge-padding-y) var(--badge-padding-x);
    border-radius: var(--badge-radius);

    font-size: var(--badge-font-size);
    font-weight: 500;

    color: var(--badge-text);
    background: var(--badge-bg);

    cursor: pointer;

    box-shadow: var(--badge-shadow);
    backdrop-filter: blur(6px);

    transition: all 0.2s ease;
}

.inline-badge:hover {
    background: var(--badge-bg-hover);
    transform: translateY(-1px);
}

.inline-badge:active {
    transform: scale(0.96);
}

/* =========================
   SVG Icon（奶茶）
========================= */
.badge-icon {
    width: 14px;
    height: 14px;
    display: inline-block;
}

/* =========================
   Dropdown（默认隐藏）
========================= */
.qr-dropdown {
    max-height: 0;
    opacity: 0;
    overflow: hidden;

    transform: translateY(-6px);

    transition:
        max-height 0.35s ease,
        opacity 0.25s ease,
        transform 0.3s ease;

    pointer-events: none;
}

details[open] .qr-dropdown {
    max-height: 260px;
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
}

/* =========================
   QR Card
========================= */
.qr-wrapper {
    margin-top: 16px;

    padding: 18px;
    border-radius: 14px;

    display: flex;
    justify-content: center;

    background: var(--glass-bg);
    backdrop-filter: blur(10px);

    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

/* QR */
.qr-img {
    width: 120px;
    border-radius: 12px;
    transition: transform 0.25s ease;
}

.qr-img:hover {
    transform: scale(1.05);
}

/* Label */
.qr-label {
    margin-top: 8px;
    font-size: 12px;
    color: #07C160;
    font-weight: 600;
}

/* Remove default arrow */
details > summary {
    list-style: none;
}
details > summary::-webkit-details-marker {
    display: none;
}
"""


class BaseComponent:
    """组件基类，提供统一的组件管理接口。"""

    def __init__(self, name: str) -> None:
        self._name = name
        self._components: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self._name

    def render(self) -> None:
        """渲染组件。子类必须实现。"""
        raise NotImplementedError("Subclass must implement render()")

    def get_component(self, key: str) -> Any:
        """获取指定名称的子组件。"""
        if key not in self._components:
            raise KeyError(f"Component '{key}' not found in {self._name}")
        return self._components[key]


class FooterPanel(BaseComponent):
    """Footer 面板组件。
    
    INTENT: 渲染页面底部的 footer，包含版权信息和打赏二维码
    INPUT: None
    OUTPUT: None (渲染到 Gradio 容器)
    SIDE EFFECT: None
    FAILURE: 抛出 Gradio 渲染异常
    """

    def __init__(self) -> None:
        super().__init__("footer")

    def render(self) -> None:
        gr.HTML(f"""
        <style>{FOOTER_CSS}</style>

        <div class="footer">

            <details>

                <summary class="footer-row">

                    <span style="font-size:13px; color:#6b7280;">
                        © 2026 <b>Sinyuk</b> · Built with passion ☕
                    </span>

                    <span class="inline-badge">

                        <!-- 奶茶 SVG（已去尺寸） -->
                        <svg class="badge-icon" viewBox="0 0 1024 1024">
                            <path d="M800 224H224l13.91 160h548.18z" fill="#F3F3F3"/>
                            <path d="M237.91 384L288 960h448l50.09-576z" fill="#F8E0B3"/>
                        </svg>

                        Support

                    </span>

                </summary>

                <div class="qr-dropdown">
                    <div class="qr-wrapper">

                        <div style="text-align:center;">
                            <img src="{WECHAT_QR_URL}" class="qr-img" loading="lazy">
                            <div class="qr-label">WeChat Pay</div>
                        </div>

                    </div>
                </div>

            </details>

        </div>
        """)


# =============================================================================
# Exports
# =============================================================================

__all__ = ["FooterPanel", "FOOTER_CSS"]
