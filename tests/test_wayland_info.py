"""Tests for Wayland protocol introspection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import wayland_info as wi_mod


class TestWaylandInfo:
    def test_returns_protocol_list(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="wl_compositor\nwl_shm\nxdg_wm_base\n",
            )
            result = wi_mod.wayland_info()

        assert result["success"] is True
        assert len(result["protocols"]) == 3

    def test_filter_by_name(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="wl_compositor\nwl_shm\nxdg_wm_base\nxdg_decoration\n",
            )
            result = wi_mod.wayland_info(filter_protocol="xdg")

        assert result["success"] is True
        assert all("xdg" in p for p in result["protocols"])
        assert len(result["protocols"]) == 2

    def test_binary_not_found(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            result = wi_mod.wayland_info()

        assert result["success"] is False
