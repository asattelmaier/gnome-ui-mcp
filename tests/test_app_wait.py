"""Tests for wait_for_app and wait_for_window (Item 8)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import app_wait


def _patch_accessibility(attr: str, return_value=None, side_effect=None):
    target = f"gnome_ui_mcp.desktop.app_wait.accessibility.{attr}"
    kwargs = {}
    if side_effect is not None:
        kwargs["side_effect"] = side_effect
    else:
        kwargs["return_value"] = return_value
    return patch(target, **kwargs)


class TestWaitForApp:
    def test_immediate_match(self) -> None:
        mock_app = MagicMock()
        mock_app.get_name.return_value = "firefox"
        apps = [(mock_app, (0,))]
        windows = {
            "success": True,
            "windows": [{"id": "0/0", "name": "Mozilla Firefox", "states": ["showing"]}],
        }
        with (
            _patch_accessibility("_select_applications", return_value=apps),
            _patch_accessibility("list_windows", return_value=windows),
        ):
            result = app_wait.wait_for_app("firefox", timeout_ms=500, poll_interval_ms=50)

        assert result["success"] is True
        assert result["app_id"] == "0"
        assert result["waited_ms"] >= 0
        assert len(result["windows"]) == 1

    def test_timeout_no_app(self) -> None:
        with _patch_accessibility("_select_applications", return_value=[]):
            result = app_wait.wait_for_app("missing-app", timeout_ms=100, poll_interval_ms=50)

        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower() or result["waited_ms"] >= 100

    def test_require_window_false(self) -> None:
        mock_app = MagicMock()
        mock_app.get_name.return_value = "myapp"
        apps = [(mock_app, (2,))]
        with _patch_accessibility("_select_applications", return_value=apps):
            result = app_wait.wait_for_app(
                "myapp", require_window=False, timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True
        assert result["app_id"] == "2"

    def test_require_window_no_showing_window(self) -> None:
        mock_app = MagicMock()
        mock_app.get_name.return_value = "myapp"
        apps = [(mock_app, (1,))]
        windows = {"success": True, "windows": []}
        with (
            _patch_accessibility("_select_applications", return_value=apps),
            _patch_accessibility("list_windows", return_value=windows),
        ):
            result = app_wait.wait_for_app("myapp", timeout_ms=100, poll_interval_ms=50)

        assert result["success"] is False

    def test_delayed_match(self) -> None:
        """App appears after a few polls."""
        mock_app = MagicMock()
        mock_app.get_name.return_value = "gedit"
        call_count = {"n": 0}

        def apps_side_effect(name):
            call_count["n"] += 1
            if call_count["n"] >= 3:
                return [(mock_app, (0,))]
            return []

        windows = {
            "success": True,
            "windows": [{"id": "0/0", "name": "gedit", "states": ["showing"]}],
        }
        with (
            _patch_accessibility("_select_applications", side_effect=apps_side_effect),
            _patch_accessibility("list_windows", return_value=windows),
        ):
            result = app_wait.wait_for_app("gedit", timeout_ms=5000, poll_interval_ms=50)

        assert result["success"] is True
        assert result["waited_ms"] > 0

    def test_returns_waited_ms(self) -> None:
        mock_app = MagicMock()
        mock_app.get_name.return_value = "app"
        apps = [(mock_app, (0,))]
        windows = {
            "success": True,
            "windows": [{"id": "0/0", "name": "w", "states": ["showing"]}],
        }
        with (
            _patch_accessibility("_select_applications", return_value=apps),
            _patch_accessibility("list_windows", return_value=windows),
        ):
            result = app_wait.wait_for_app("app", timeout_ms=500, poll_interval_ms=50)

        assert "waited_ms" in result
        assert isinstance(result["waited_ms"], int | float)


class TestWaitForWindow:
    def test_immediate_find(self) -> None:
        matches = {
            "success": True,
            "matches": [{"id": "0/1", "name": "My Window", "role": "frame"}],
        }
        with _patch_accessibility("find_elements", return_value=matches):
            result = app_wait.wait_for_window("My Window", timeout_ms=500, poll_interval_ms=50)

        assert result["success"] is True
        assert result["window"]["id"] == "0/1"

    def test_timeout_no_window(self) -> None:
        with _patch_accessibility("find_elements", return_value={"success": True, "matches": []}):
            result = app_wait.wait_for_window("nonexistent", timeout_ms=100, poll_interval_ms=50)

        assert result["success"] is False

    def test_with_app_name(self) -> None:
        matches = {
            "success": True,
            "matches": [{"id": "0/0", "name": "File", "role": "frame"}],
        }
        with _patch_accessibility("find_elements", return_value=matches) as mock_find:
            result = app_wait.wait_for_window(
                "File", app_name="nautilus", timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True
        mock_find.assert_called()

    def test_with_role(self) -> None:
        matches = {
            "success": True,
            "matches": [{"id": "0/0", "name": "Alert", "role": "dialog"}],
        }
        with _patch_accessibility("find_elements", return_value=matches) as mock_find:
            result = app_wait.wait_for_window(
                "Alert", role="dialog", timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True
        call_kwargs = mock_find.call_args
        assert call_kwargs is not None

    def test_delayed_window(self) -> None:
        call_count = {"n": 0}

        def find_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] >= 3:
                return {
                    "success": True,
                    "matches": [{"id": "1/0", "name": "Popup", "role": "dialog"}],
                }
            return {"success": True, "matches": []}

        with _patch_accessibility("find_elements", side_effect=find_side_effect):
            result = app_wait.wait_for_window("Popup", timeout_ms=5000, poll_interval_ms=50)

        assert result["success"] is True
        assert result["waited_ms"] > 0

    def test_returns_waited_ms(self) -> None:
        matches = {
            "success": True,
            "matches": [{"id": "0/0", "name": "Win", "role": "frame"}],
        }
        with _patch_accessibility("find_elements", return_value=matches):
            result = app_wait.wait_for_window("Win", timeout_ms=200, poll_interval_ms=50)

        assert "waited_ms" in result
        assert isinstance(result["waited_ms"], int | float)
