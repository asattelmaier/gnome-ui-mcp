"""State management, OCR, and visual analysis.

Wraps desktop modules. Returns typed data and raises exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import ocr as _desktop_ocr
from ..desktop import snapshots as _desktop_snapshots
from ..desktop import visual as _desktop_visual
from ..desktop import vlm as _desktop_vlm


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


# -- dataclasses --


@dataclass
class SnapshotResult:
    snapshot_id: str


@dataclass
class CompareStateResult:
    apps_added: list[dict]
    apps_removed: list[dict]
    windows_added: list[dict]
    windows_removed: list[dict]
    focus_changed: bool
    popups_changed: bool


@dataclass
class OcrResult:
    text: str
    words: list[dict]
    word_count: int
    screenshot_path: str


@dataclass
class FindTextOcrResult:
    target: str
    found: bool
    matches: list[dict]
    match_count: int


@dataclass
class ClickTextOcrResult:
    target: str
    ocr_match: dict
    input_injected: bool
    effect_verified: bool | None


@dataclass
class TypeIntoResult:
    label: str
    method: str
    element_id: str | None


@dataclass
class AnalysisResult:
    analysis: str
    provider: str
    model: str


@dataclass
class CompareScreenshotsResult:
    analysis: str
    provider: str
    model: str
    path1: str
    path2: str


@dataclass
class PixelColor:
    x: int
    y: int
    r: int
    g: int
    b: int
    a: int
    hex: str


@dataclass
class RegionColor:
    x: int
    y: int
    width: int
    height: int
    r: int
    g: int
    b: int
    a: int
    hex: str


@dataclass
class VisualDiffResult:
    changed: bool
    changed_percent: float
    changed_pixels: int
    total_pixels: int
    regions: list[dict]
    region_count: int


@dataclass
class ActionHistoryResult:
    actions: list[dict]
    count: int


# -- public API --


def snapshot_state() -> SnapshotResult:
    """Capture desktop state snapshot. Raises on failure."""
    result = _require(_desktop_snapshots.snapshot_state())
    return SnapshotResult(snapshot_id=result.get("snapshot_id", ""))


def compare_state(before_id: str, after_id: str) -> CompareStateResult:
    """Compare two snapshots. Raises on failure."""
    result = _require(_desktop_snapshots.compare_state(before_id=before_id, after_id=after_id))
    return CompareStateResult(
        apps_added=result.get("apps_added", []),
        apps_removed=result.get("apps_removed", []),
        windows_added=result.get("windows_added", []),
        windows_removed=result.get("windows_removed", []),
        focus_changed=result.get("focus_changed", False),
        popups_changed=result.get("popups_changed", False),
    )


def ocr_screen(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> OcrResult:
    """Extract text via OCR. Raises on failure."""
    result = _require(_desktop_ocr.ocr_screen(x=x, y=y, width=width, height=height))
    return OcrResult(
        text=result.get("text", ""),
        words=result.get("words", []),
        word_count=result.get("word_count", 0),
        screenshot_path=result.get("screenshot_path", ""),
    )


def find_text_ocr(
    target: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> FindTextOcrResult:
    """Find text on screen via OCR. Raises on failure."""
    result = _require(
        _desktop_ocr.find_text_ocr(
            target=target,
            x=x,
            y=y,
            width=width,
            height=height,
        )
    )
    matches = result.get("matches", [])
    return FindTextOcrResult(
        target=target,
        found=len(matches) > 0,
        matches=matches,
        match_count=len(matches),
    )


def click_text_ocr(target: str, button: str = "left") -> ClickTextOcrResult:
    """Find text via OCR and click it. Raises on failure."""
    result = _require(_desktop_ocr.click_text_ocr(target=target, button=button))
    return ClickTextOcrResult(
        target=target,
        ocr_match=result.get("ocr_match", {}),
        input_injected=result.get("input_injected", False),
        effect_verified=result.get("effect_verified"),
    )


def type_into(label: str, text: str, submit: bool = False) -> TypeIntoResult:
    """Find an input field by label and type into it. Raises on failure."""
    result = _require(_desktop_ocr.type_into(label=label, text=text, submit=submit))
    return TypeIntoResult(
        label=label,
        method=result.get("method", ""),
        element_id=result.get("element_id"),
    )


def analyze_screenshot(
    prompt: str,
    provider: str = "openrouter",
    model: str | None = None,
) -> AnalysisResult:
    """Analyze screenshot with VLM. Raises on failure."""
    result = _require(
        _desktop_vlm.analyze_screenshot(
            prompt=prompt,
            provider=provider,
            model=model,
        )
    )
    return AnalysisResult(
        analysis=result.get("analysis", ""),
        provider=result.get("provider", provider),
        model=result.get("model", ""),
    )


def compare_screenshots(
    path1: str,
    path2: str,
    prompt: str | None = None,
    provider: str = "openrouter",
    model: str | None = None,
) -> CompareScreenshotsResult:
    """Compare two screenshots with VLM. Raises on failure."""
    result = _require(
        _desktop_vlm.compare_screenshots(
            path1=path1,
            path2=path2,
            prompt=prompt,
            provider=provider,
            model=model,
        )
    )
    return CompareScreenshotsResult(
        analysis=result.get("analysis", ""),
        provider=result.get("provider", provider),
        model=result.get("model", ""),
        path1=path1,
        path2=path2,
    )


def get_pixel_color(x: int, y: int) -> PixelColor:
    """Get pixel color at coordinates. Raises on failure."""
    result = _require(_desktop_visual.get_pixel_color(x=x, y=y))
    return PixelColor(
        x=x,
        y=y,
        r=result.get("r", 0),
        g=result.get("g", 0),
        b=result.get("b", 0),
        a=result.get("a", 255),
        hex=result.get("hex", "#000000"),
    )


def get_region_color(x: int, y: int, width: int, height: int) -> RegionColor:
    """Get average color of a region. Raises on failure."""
    result = _require(_desktop_visual.get_region_color(x=x, y=y, width=width, height=height))
    return RegionColor(
        x=x,
        y=y,
        width=width,
        height=height,
        r=result.get("r", 0),
        g=result.get("g", 0),
        b=result.get("b", 0),
        a=result.get("a", 255),
        hex=result.get("hex", "#000000"),
    )


def visual_diff(
    image_path_1: str,
    image_path_2: str,
    threshold: int = 30,
) -> VisualDiffResult:
    """Compare two images pixel-by-pixel. Raises on failure."""
    result = _require(
        _desktop_visual.visual_diff(
            image_path_1=image_path_1,
            image_path_2=image_path_2,
            threshold=threshold,
        )
    )
    return VisualDiffResult(
        changed=result.get("changed", False),
        changed_percent=result.get("changed_percent", 0.0),
        changed_pixels=result.get("changed_pixels", 0),
        total_pixels=result.get("total_pixels", 0),
        regions=result.get("regions", []),
        region_count=result.get("region_count", 0),
    )
