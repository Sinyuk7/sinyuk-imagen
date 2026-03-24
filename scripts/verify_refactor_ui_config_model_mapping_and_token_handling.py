"""Manual verification checklist for this change.

This project currently does not ship an automated test suite for these flows.
This script provides a repeatable, step-by-step verification plan that matches
OpenSpec tasks 5.1~5.5.

Run:
  python scripts/verify_refactor_ui_config_model_mapping_and_token_handling.py

Notes:
- Some steps require launching the UI and visually confirming behavior.
- Do NOT paste real tokens into logs/screenshots.
"""

from __future__ import annotations

import copy
import json
import os
import sys

# Ensure repo root is on sys.path when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _print(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def verify_5_1_config_validation() -> None:
    _print("5.1 Config validation")
    print("- [ ] Start app with a provider.models as LIST (old format) -> startup MUST fail")
    print("      Expected: error mentions models must be mapping display_name -> model_name")
    print("      Expected: error includes an example mapping")
    print("- [ ] Remove provider.hint -> startup MUST succeed")


def verify_5_2_model_mapping() -> None:
    _print("5.2 Model mapping")
    print("- [ ] In UI, model dropdown shows DISPLAY NAMES (dict keys)")
    print("- [ ] In provider request, real model name is used (dict value)")
    print("      Tip: enable Debug Mode (Dry Run) and confirm debug snapshot has:")
    print("           model_display_name=<UI selection> and model_name=<real model>")


def verify_5_3_token_priority_and_masking() -> None:
    _print("5.3 Token priority & masking")
    print("- [ ] Enter token in UI -> overrides config/env")
    print("- [ ] Clear UI token -> falls back to config/env")
    print("- [ ] No plaintext token appears in:")
    print("      - UI status bar")
    print("      - Debug Output")
    print("      - logs")


def verify_5_4_debug_dry_run_snapshot() -> None:
    _print("5.4 Debug Mode (Dry Run)")
    print("- [ ] Enable Debug Mode (Dry Run) -> no real request is sent")
    print("- [ ] Debug Output shows Postman-style HTTP request JSON")
    print("- [ ] Authorization header is masked as '***'")
    print("- [ ] Provider returns actual REST API request format")

    # Note: Debug snapshot is now built by each Provider, not ImageService.
    # The snapshot format is Postman-style HTTP request:
    # {
    #   "method": "POST",
    #   "url": "...",
    #   "headers": {"Authorization": "***", ...},
    #   "body": {...}
    # }


def verify_5_5_regression() -> None:
    _print("5.5 Regression")
    print("- [ ] Debug Mode OFF -> normal generation works")
    print("- [ ] Switch providers multiple times -> no UI regressions")
    print("- [ ] Parameter settings remain functional")


def main() -> None:
    verify_5_1_config_validation()
    verify_5_2_model_mapping()
    verify_5_3_token_priority_and_masking()
    verify_5_4_debug_dry_run_snapshot()
    verify_5_5_regression()


if __name__ == "__main__":
    main()
