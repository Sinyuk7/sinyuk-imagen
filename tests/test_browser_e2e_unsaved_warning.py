"""Browser-level E2E coverage for the session unsaved-warning flow."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_BROWSER_E2E") != "1",
    reason="Set RUN_BROWSER_E2E=1 to run browser-level E2E tests.",
)

playwright = pytest.importorskip("playwright.sync_api")

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ENTRY = REPO_ROOT / "app.py"
CHROME_EXECUTABLE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.25)
    raise AssertionError(f"Timed out waiting for app server at {url}")


@pytest.fixture()
def launched_app() -> tuple[subprocess.Popen[str], str]:
    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}/"
    env = os.environ.copy()
    env["GRADIO_SERVER_NAME"] = "127.0.0.1"
    env["GRADIO_SERVER_PORT"] = str(port)
    env["GRADIO_ANALYTICS_ENABLED"] = "False"
    process = subprocess.Popen(
        [sys.executable, str(APP_ENTRY)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        _wait_for_server(base_url)
        yield process, base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_unsaved_warning_dialog_clears_after_mark_all_saved(
    launched_app: tuple[subprocess.Popen[str], str],
) -> None:
    if not Path(CHROME_EXECUTABLE).exists():
        pytest.skip("Google Chrome is not installed at the expected path.")

    _, base_url = launched_app
    sync_playwright = playwright.sync_playwright

    with sync_playwright() as runner:
        try:
            browser = runner.chromium.launch(
                executable_path=CHROME_EXECUTABLE,
                headless=True,
                args=["--no-sandbox"],
            )
        except Exception as exc:
            pytest.skip(f"Could not launch Chrome for browser E2E: {exc}")

        page = browser.new_page()
        try:
            page.goto(base_url, wait_until="load")
            page.locator("#prompt-input textarea").fill("A dry-run browser e2e prompt")
            page.get_by_text("Advanced Settings").first.click()
            page.locator("#debug-mode-toggle input").check(force=True)
            page.locator("#generate-button").click()

            page.locator("#session-warning-banner").wait_for(state="visible")
            page.locator("#task-history-list [data-task-id]").first.wait_for()
            assert "[UNSAVED]" in page.locator("#task-history-list").text_content()

            unsaved_dialogs: list[str] = []

            def dismiss_dialog(dialog) -> None:
                unsaved_dialogs.append(dialog.type)
                dialog.dismiss()

            page.once("dialog", dismiss_dialog)
            try:
                page.goto("about:blank", wait_until="load", timeout=3_000)
            except Exception:
                pass

            assert "beforeunload" in unsaved_dialogs
            assert not page.url.startswith("about:blank")

            page.locator("#mark-all-saved-button").click()
            page.locator("#session-warning-banner").wait_for(state="hidden")
            assert "[Saved]" in page.locator("#task-history-list").text_content()

            cleared_dialogs: list[str] = []
            page.once("dialog", lambda dialog: cleared_dialogs.append(dialog.type))
            page.goto("about:blank", wait_until="load")
            assert cleared_dialogs == []
            assert page.url.startswith("about:blank")
        finally:
            page.close()
            browser.close()
