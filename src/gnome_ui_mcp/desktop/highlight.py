"""Annotate a screenshot with element highlight (Item 16)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from . import accessibility, input

JsonDict = dict[str, Any]

try:
    from PIL import Image, ImageDraw  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment,misc]
    ImageDraw = None  # type: ignore[assignment,misc]

CACHE_DIR = Path.home() / ".cache" / "gnome-ui-mcp" / "highlights"


def highlight_element(
    element_id: str,
    color: str = "red",
    label: str | None = None,
) -> JsonDict:
    """Take a screenshot and draw a rectangle around *element_id*.

    Returns the path to the annotated image.
    """
    if Image is None:
        return {"success": False, "error": "Pillow is not installed"}

    try:
        acc = accessibility._resolve_element(element_id)
    except (ValueError, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}

    bounds = accessibility._element_bounds(acc)
    if bounds is None:
        return {"success": False, "error": "Element has no bounds"}

    shot = input.screenshot()
    if not shot.get("success"):
        return {"success": False, "error": shot.get("error", "Screenshot failed")}

    src_path = str(shot["path"])
    img = Image.open(src_path)
    draw = ImageDraw.Draw(img)

    x, y, w, h = int(bounds["x"]), int(bounds["y"]), int(bounds["width"]), int(bounds["height"])
    draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

    if label:
        draw.text((x, max(0, y - 16)), label, fill=color)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CACHE_DIR / f"highlight-{int(time.time() * 1000)}.png"
    img.save(str(out_path))

    return {
        "success": True,
        "path": str(out_path),
        "element_id": element_id,
        "bounds": bounds,
    }
