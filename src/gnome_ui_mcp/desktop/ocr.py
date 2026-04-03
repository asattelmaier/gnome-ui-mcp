from __future__ import annotations

from . import accessibility, input, interaction
from .types import JsonDict

try:
    from PIL import Image, ImageFilter, ImageOps

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

try:
    import pytesseract

    _HAS_TESSERACT = True
except ImportError:
    _HAS_TESSERACT = False

_HAS_OCR_DEPS = _HAS_PIL and _HAS_TESSERACT

_MISSING_DEPS_ERROR = (
    "OCR tools require pytesseract and Pillow. Install them with: pip install 'gnome-ui-mcp[ocr]'"
)


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    gray = img.convert("L")
    pixels = list(gray.getdata())
    avg_brightness = sum(pixels) / len(pixels) if pixels else 128
    if avg_brightness < 128:
        gray = ImageOps.invert(gray)
    return gray.filter(ImageFilter.SHARPEN)


def _filter_words(raw_data: dict, min_conf: int = 30) -> list[JsonDict]:
    words: list[JsonDict] = []
    n = len(raw_data.get("text", []))
    for i in range(n):
        text = str(raw_data["text"][i]).strip()
        conf = int(raw_data["conf"][i])
        if not text or conf < min_conf:
            continue
        words.append(
            {
                "text": text,
                "x": int(raw_data["left"][i]),
                "y": int(raw_data["top"][i]),
                "width": int(raw_data["width"][i]),
                "height": int(raw_data["height"][i]),
                "confidence": conf,
            }
        )
    return words


def _find_text_in_words(words: list[JsonDict], target: str) -> list[JsonDict]:
    target_lower = target.lower()
    target_parts = target_lower.split()
    matches: list[JsonDict] = []

    if len(target_parts) <= 1:
        for w in words:
            if target_lower in w["text"].lower():
                matches.append(
                    {
                        "text": w["text"],
                        "x": w["x"],
                        "y": w["y"],
                        "width": w["width"],
                        "height": w["height"],
                        "center_x": w["x"] + w["width"] // 2,
                        "center_y": w["y"] + w["height"] // 2,
                    }
                )
        return matches

    for i in range(len(words) - len(target_parts) + 1):
        candidate = " ".join(words[i + j]["text"] for j in range(len(target_parts)))
        if candidate.lower() == target_lower:
            first = words[i]
            last = words[i + len(target_parts) - 1]
            x = first["x"]
            y = min(words[i + j]["y"] for j in range(len(target_parts)))
            right = last["x"] + last["width"]
            bottom = max(
                words[i + j]["y"] + words[i + j]["height"] for j in range(len(target_parts))
            )
            width = right - x
            height = bottom - y
            matches.append(
                {
                    "text": candidate,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "center_x": x + width // 2,
                    "center_y": y + height // 2,
                }
            )
    return matches


def ocr_screen(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> JsonDict:
    if not _HAS_OCR_DEPS:
        return {"success": False, "error": _MISSING_DEPS_ERROR}
    is_region = all(v is not None for v in (x, y, width, height))
    if is_region:
        shot = input.screenshot_area(x, y, width, height)
    else:
        shot = input.screenshot()

    if not shot.get("success"):
        return {"success": False, "error": f"Screenshot failed: {shot.get('error', 'unknown')}"}

    path = shot["path"]
    img = Image.open(path)
    processed = _preprocess_for_ocr(img)

    raw_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
    words = _filter_words(raw_data)

    if is_region:
        for w in words:
            w["x"] += x
            w["y"] += y
            if "center_x" in w:
                w["center_x"] += x
            if "center_y" in w:
                w["center_y"] += y

    full_text = pytesseract.image_to_string(processed).strip()

    return {
        "success": True,
        "text": full_text,
        "words": words,
        "word_count": len(words),
        "screenshot_path": path,
    }


def find_text_ocr(
    target: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> JsonDict:
    screen = ocr_screen(x=x, y=y, width=width, height=height)
    if not screen.get("success"):
        return screen

    matches = _find_text_in_words(screen["words"], target)
    return {
        "success": True,
        "target": target,
        "matches": matches,
        "match_count": len(matches),
    }


def click_text_ocr(target: str, button: str = "left") -> JsonDict:
    found = find_text_ocr(target)
    if not found.get("success"):
        return found

    matches = found.get("matches", [])
    if not matches:
        return {"success": False, "error": f"Text {target!r} not found on screen"}

    match = matches[0]
    click_result = interaction.click_at(x=match["center_x"], y=match["center_y"], button=button)
    click_result["ocr_match"] = match
    return click_result


def type_into(label: str, text: str, submit: bool = False) -> JsonDict:
    """Find an input field by label and type text into it.

    Strategy:
    1. **AT-SPI first** -- search for visible elements matching label, filter
       for those with an "editable" state, focus it and type.
    2. **OCR fallback** -- use find_text_ocr to locate the label on screen,
       click its center, then type.
    3. If submit is True, press Return after typing.
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
            "label": label,
            "element_id": editable_match["id"],
        }

    # --- OCR fallback ---
    ocr_result = find_text_ocr(label)
    if not ocr_result or not ocr_result.get("success"):
        return {"success": False, "error": f"Label {label!r} not found via AT-SPI or OCR"}

    matches = ocr_result.get("matches", [])
    if not matches:
        return {"success": False, "error": f"Label {label!r} not found via OCR"}
    match = matches[0]
    center_x = match["center_x"]
    center_y = match["center_y"]

    interaction.click_at(x=center_x, y=center_y)
    input.type_text(text)
    if submit:
        input.press_key("Return")
    return {
        "success": True,
        "method": "ocr",
        "label": label,
    }
