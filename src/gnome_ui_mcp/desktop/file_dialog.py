from __future__ import annotations

import time
from typing import Any

from . import input

JsonDict = dict[str, Any]


def file_dialog_set_path(path: str) -> JsonDict:
    """Set a file path in a GTK file dialog by activating the location entry."""
    if not path:
        return {"success": False, "error": "Path must not be empty"}

    # Activate the location entry bar with Ctrl+L
    combo_result = input.key_combo("ctrl+l")
    if not combo_result.get("success"):
        return {
            "success": False,
            "error": "Failed to activate location entry (Ctrl+L)",
            "combo_result": combo_result,
        }

    time.sleep(0.3)

    # Type the path
    type_result = input.type_text(path)
    if not type_result.get("success"):
        return {
            "success": False,
            "error": "Failed to type path",
            "type_result": type_result,
        }

    time.sleep(0.1)

    # Press Return to confirm
    key_result = input.press_key("Return")
    if not key_result.get("success"):
        return {
            "success": False,
            "error": "Failed to press Return",
            "key_result": key_result,
        }

    return {
        "success": True,
        "path": path,
    }
