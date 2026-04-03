"""Tests for screenshot return_base64 parameter."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


def _fake_screenshot_dbus(output_path: str) -> tuple[bool, str]:
    """Write a tiny fake PNG and return success."""
    # Minimal valid PNG (1x1 transparent pixel)
    import struct
    import zlib

    def _make_png() -> bytes:
        sig = b"\x89PNG\r\n\x1a\n"

        def chunk(ctype: bytes, data: bytes) -> bytes:
            c = ctype + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        raw = zlib.compress(b"\x00\x00\x00\x00")
        return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")

    data = _make_png()
    with open(output_path, "wb") as f:
        f.write(data)
    return True, output_path


class TestScreenshotBase64:
    def test_base64_included_when_requested(self) -> None:
        with (
            patch.object(input_mod, "_validate_screenshot_path") as mock_validate,
            patch.object(input_mod, "_screenshot_dbus", side_effect=_fake_screenshot_dbus),
            patch.object(input_mod, "get_display_scale_factor", return_value=1),
            patch.object(input_mod, "Image", None),
        ):
            import tempfile
            from pathlib import Path

            out = Path(tempfile.mktemp(suffix=".png"))
            mock_validate.return_value = out
            result = input_mod.screenshot(return_base64=True)

        assert result["success"] is True
        assert "image_base64" in result
        # Verify it's valid base64
        decoded = base64.b64decode(result["image_base64"])
        assert decoded[:4] == b"\x89PNG"

    def test_base64_not_included_by_default(self) -> None:
        with (
            patch.object(input_mod, "_validate_screenshot_path") as mock_validate,
            patch.object(input_mod, "_screenshot_dbus", side_effect=_fake_screenshot_dbus),
            patch.object(input_mod, "get_display_scale_factor", return_value=1),
            patch.object(input_mod, "Image", None),
        ):
            import tempfile
            from pathlib import Path

            out = Path(tempfile.mktemp(suffix=".png"))
            mock_validate.return_value = out
            result = input_mod.screenshot(return_base64=False)

        assert result["success"] is True
        assert "image_base64" not in result

    def test_base64_with_pil(self) -> None:
        mock_img = MagicMock()
        mock_img.size = (100, 100)
        mock_image_mod = MagicMock()
        mock_image_mod.open.return_value = mock_img

        with (
            patch.object(input_mod, "_validate_screenshot_path") as mock_validate,
            patch.object(input_mod, "_screenshot_dbus", side_effect=_fake_screenshot_dbus),
            patch.object(input_mod, "get_display_scale_factor", return_value=1),
            patch.object(input_mod, "Image", mock_image_mod),
        ):
            import tempfile
            from pathlib import Path

            out = Path(tempfile.mktemp(suffix=".png"))
            mock_validate.return_value = out
            result = input_mod.screenshot(return_base64=True)

        assert result["success"] is True
        assert "image_base64" in result
