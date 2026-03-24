"""Sinyuk Imagen: entry point.

This file ONLY handles:
1. Load .env
2. Setup logging
3. Initialize the core facade runtime
4. Build the Gradio app
5. Build and launch Gradio app

NO business logic belongs here.
"""

import atexit
import logging
import signal
import sys

from dotenv import load_dotenv
from gradio import themes

import core.api as core_api
from ui.app import build_app


def main():
    # ── 1. Load environment variables ──────────────────────────────
    load_dotenv()

    # ── 2. Setup logging ───────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    # ── 3. Initialize core runtime (triggers config validation) ───
    try:
        core_api.initialize_runtime()
        ui_context = core_api.get_ui_context()
    except Exception as exc:
        logger.error("Startup error: %s", exc)
        sys.exit(1)

    atexit.register(core_api.begin_shutdown)

    def _handle_sigterm(signum, frame) -> None:
        logger.info("Received SIGTERM, beginning graceful shutdown...")
        core_api.begin_shutdown(
            reason="Task manager is shutting down. Please try again later."
        )
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)

    # ── 5. Build and launch Gradio app ─────────────────────────────
    app = build_app(ui_context)
    logger.info("Starting %s...", ui_context.title)

    app.launch(theme=themes.Soft())


if __name__ == "__main__":
    main()
