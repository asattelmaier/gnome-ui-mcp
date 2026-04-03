from __future__ import annotations

from pathlib import Path

from . import input
from .input import CACHE_DIR
from .types import JsonDict

try:
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    _HAS_VISUAL_DEPS = True
except ImportError:
    _HAS_VISUAL_DEPS = False

_MISSING_DEPS_ERROR = (
    "Visual tools require numpy, scipy, and Pillow. "
    "Install them with: pip install 'gnome-ui-mcp[visual]'"
)


def get_pixel_color(x: int, y: int) -> JsonDict:
    if not _HAS_VISUAL_DEPS:
        return {"success": False, "error": _MISSING_DEPS_ERROR}
    shot = input.screenshot()
    if not shot.get("success"):
        return {"success": False, "error": f"Screenshot failed: {shot.get('error', 'unknown')}"}

    img = Image.open(shot["path"])
    if x < 0 or y < 0 or x >= img.width or y >= img.height:
        return {
            "success": False,
            "error": f"Coordinates ({x}, {y}) out of bounds (image: {img.width}x{img.height})",
        }

    pixel = img.getpixel((x, y))
    if isinstance(pixel, int):
        r, g, b, a = pixel, pixel, pixel, 255
    elif len(pixel) == 3:
        r, g, b = pixel
        a = 255
    else:
        r, g, b, a = pixel

    return {
        "success": True,
        "x": x,
        "y": y,
        "r": r,
        "g": g,
        "b": b,
        "a": a,
        "hex": f"#{r:02X}{g:02X}{b:02X}",
    }


def get_region_color(x: int, y: int, width: int, height: int) -> JsonDict:
    if not _HAS_VISUAL_DEPS:
        return {"success": False, "error": _MISSING_DEPS_ERROR}
    shot = input.screenshot()
    if not shot.get("success"):
        return {"success": False, "error": f"Screenshot failed: {shot.get('error', 'unknown')}"}

    img = Image.open(shot["path"])
    region = img.crop((x, y, x + width, y + height))
    arr = np.array(region)

    if arr.ndim == 2:
        avg = float(arr.mean())
        r = g = b = int(round(avg))
        a = 255
    else:
        means = arr.mean(axis=(0, 1))
        r, g, b = int(round(means[0])), int(round(means[1])), int(round(means[2]))
        a = int(round(means[3])) if arr.shape[2] == 4 else 255

    return {
        "success": True,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "r": r,
        "g": g,
        "b": b,
        "a": a,
        "hex": f"#{r:02X}{g:02X}{b:02X}",
    }


def visual_diff(
    image_path_1: str,
    image_path_2: str,
    threshold: int = 30,
) -> JsonDict:
    if not _HAS_VISUAL_DEPS:
        return {"success": False, "error": _MISSING_DEPS_ERROR}

    for p in (image_path_1, image_path_2):
        try:
            Path(p).resolve().relative_to(CACHE_DIR.resolve())
        except ValueError:
            return {
                "success": False,
                "error": f"Path outside screenshot cache directory: {p}",
            }

    try:
        img1 = Image.open(image_path_1).convert("RGB")
        img2 = Image.open(image_path_2).convert("RGB")
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    arr1 = np.array(img1, dtype=np.int16)
    arr2 = np.array(img2, dtype=np.int16)

    diff = np.abs(arr1 - arr2)
    binary = diff.sum(axis=2) > threshold
    total_pixels = binary.size
    changed_pixels = int(binary.sum())
    changed_percent = round(changed_pixels / total_pixels * 100, 2) if total_pixels else 0.0

    if changed_pixels == 0:
        return {
            "success": True,
            "changed": False,
            "changed_percent": 0.0,
            "changed_pixels": 0,
            "total_pixels": total_pixels,
            "regions": [],
        }

    labeled, num_regions = ndimage.label(binary)
    regions: list[JsonDict] = []
    for i in range(1, num_regions + 1):
        ys, xs = np.where(labeled == i)
        if len(xs) < 5:
            continue
        regions.append(
            {
                "x": int(xs.min()),
                "y": int(ys.min()),
                "width": int(xs.max() - xs.min() + 1),
                "height": int(ys.max() - ys.min() + 1),
                "pixel_count": len(xs),
            }
        )

    return {
        "success": True,
        "changed": True,
        "changed_percent": changed_percent,
        "changed_pixels": changed_pixels,
        "total_pixels": total_pixels,
        "regions": regions,
        "region_count": len(regions),
    }
