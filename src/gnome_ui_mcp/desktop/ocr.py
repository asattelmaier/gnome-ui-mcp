"""OCR-assisted typing: find a label on screen and type into its field."""

from __future__ import annotations

import subprocess
from typing import Any

from . import accessibility, input, interaction

JsonDict = dict[str, Any]


def find_text_ocr(label: str) -> JsonDict | None:
    """Use Tesseract OCR to locate *label* on the current screen.

    Returns a bounding-box dict ``{"x", "y", "width", "height"}`` for the
    first match, or ``None`` if the label is not found.
    """
    screenshot_result = input.screenshot()
    if not screenshot_result.get("success"):
        return None

    path = screenshot_result["path"]
    try:
        proc = subprocess.run(
            ["tesseract", path, "stdout", "tsv"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if proc.returncode != 0:
        return None

    needle = label.casefold()
    for line in proc.stdout.splitlines()[1:]:  # skip header
        parts = line.split("\t")
        if len(parts) < 12:
            continue
        text = parts[11].strip()
        if needle in text.casefold():
            try:
                return {
                    "x": int(parts[6]),
                    "y": int(parts[7]),
                    "width": int(parts[8]),
                    "height": int(parts[9]),
                }
            except (ValueError, IndexError):
                continue
    return None


def type_into(label: str, text: str, *, submit: bool = False) -> JsonDict:
    """Find an input field by *label* and type *text* into it.

    Strategy:
    1. **AT-SPI first** -- search for visible elements matching *label*, filter
       for those with an ``"editable"`` state, focus it and type.
    2. **OCR fallback** -- use ``find_text_ocr`` to locate the label on screen,
       click its centre, then type.
    3. If *submit* is ``True``, press Return after typing.
    """
    # --- AT-SPI path ---
    search = accessibility.find_elements(query=label, showing_only=True)
    editable_match: JsonDict | None = None
    for match in search.get("matches", []):
        if "editable" in match.get("states", []):
            editable_match = match
            break

    if editable_match is not None:
        accessibility.focus_element(str(editable_match["id"]))
        input.type_text(text)
        if submit:
            input.press_key("Return")
        return {
            "success": True,
            "method": "atspi",
            "action": "type_into",
            "label": label,
            "element_id": editable_match["id"],
        }

    # --- OCR fallback path ---
    ocr_box = find_text_ocr(label)
    if ocr_box is not None:
        center_x = ocr_box["x"] + ocr_box["width"] // 2
        center_y = ocr_box["y"] + ocr_box["height"] // 2
        interaction.click_at(x=center_x, y=center_y)
        input.type_text(text)
        if submit:
            input.press_key("Return")
        return {
            "success": True,
            "method": "ocr",
            "action": "type_into",
            "label": label,
            "ocr_bounds": ocr_box,
        }

    return {
        "success": False,
        "action": "type_into",
        "error": f"Label not found via AT-SPI or OCR: {label!r}",
    }
