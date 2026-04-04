"""Input functions returning typed results.

Wraps the v1 desktop.input module. Returns dataclasses and raises
exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import input as _v1


@dataclass
class ScreenshotInfo:
    available: bool
    backend: str | None = None
    interface: str | None = None
    error: str | None = None


@dataclass
class RemoteInputInfo:
    available: bool
    version: int | None = None
    supported_device_types: int | None = None
    error: str | None = None


@dataclass
class ScreenshotResult:
    path: str
    scale_factor: int
    pixel_size: list[int] | None = None
    logical_size: list[int] | None = None
    image_base64: str | None = None


def screenshot_info() -> ScreenshotInfo:
    result = _v1.screenshot_info()
    return ScreenshotInfo(
        available=bool(result.get("available", False)),
        backend=result.get("backend"),
        interface=result.get("interface"),
        error=result.get("error"),
    )


def remote_input_info() -> RemoteInputInfo:
    result = _v1.remote_input_info()
    return RemoteInputInfo(
        available=bool(result.get("available", False)),
        version=result.get("version"),
        supported_device_types=result.get("supported_device_types"),
        error=result.get("error"),
    )


def screenshot(
    filename: str | None = None,
    return_base64: bool = False,
) -> ScreenshotResult:
    """Take a screenshot. Raises on failure."""
    result = _v1.screenshot(filename=filename, return_base64=return_base64)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Screenshot failed")))

    return ScreenshotResult(
        path=str(result["path"]),
        scale_factor=int(result.get("scale_factor", 1)),
        pixel_size=result.get("pixel_size"),
        logical_size=result.get("logical_size"),
        image_base64=result.get("image_base64"),
    )
