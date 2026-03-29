"""Tests for generic D-Bus call tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import dbus as dbus_mod


class TestVariantFromJson:
    def test_string_arg(self) -> None:
        v = dbus_mod._build_variant("(s)", ["hello"])
        assert v.unpack() == ("hello",)

    def test_int_arg(self) -> None:
        v = dbus_mod._build_variant("(i)", [42])
        assert v.unpack() == (42,)

    def test_uint_arg(self) -> None:
        v = dbus_mod._build_variant("(u)", [42])
        assert v.unpack() == (42,)

    def test_bool_arg(self) -> None:
        v = dbus_mod._build_variant("(b)", [True])
        assert v.unpack() == (True,)

    def test_double_arg(self) -> None:
        v = dbus_mod._build_variant("(d)", [3.14])
        result = v.unpack()
        assert abs(result[0] - 3.14) < 0.001

    def test_string_array(self) -> None:
        v = dbus_mod._build_variant("(as)", [["a", "b", "c"]])
        assert v.unpack() == (["a", "b", "c"],)

    def test_no_args(self) -> None:
        result = dbus_mod._build_variant(None, None)
        assert result is None

    def test_empty_signature(self) -> None:
        result = dbus_mod._build_variant("", [])
        assert result is None


class TestVariantToJson:
    def test_string(self) -> None:
        from gi.repository import GLib

        v = GLib.Variant("(s)", ("hello",))
        result = dbus_mod._variant_to_json(v)
        assert result == ("hello",)

    def test_nested_dict(self) -> None:
        from gi.repository import GLib

        v = GLib.Variant("(a{sv})", ({"key": GLib.Variant("s", "val")},))
        result = dbus_mod._variant_to_json(v)
        assert result == ({"key": "val"},)

    def test_int(self) -> None:
        from gi.repository import GLib

        v = GLib.Variant("(iu)", (42, 99))
        result = dbus_mod._variant_to_json(v)
        assert result == (42, 99)


class TestDbusCall:
    def test_call_with_no_args(self) -> None:
        with patch("gnome_ui_mcp.desktop.dbus.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant(
                "(ssss)", ("GNOME Shell", "GNOME", "46.0", "1.2")
            )

            result = dbus_mod.dbus_call(
                bus_name="org.freedesktop.Notifications",
                object_path="/org/freedesktop/Notifications",
                interface="org.freedesktop.Notifications",
                method="GetServerInformation",
            )

        assert result["success"] is True
        assert result["result"] == ("GNOME Shell", "GNOME", "46.0", "1.2")

    def test_call_with_string_arg(self) -> None:
        with patch("gnome_ui_mcp.desktop.dbus.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(b)", (True,))

            result = dbus_mod.dbus_call(
                bus_name="org.example",
                object_path="/org/example",
                interface="org.example.Iface",
                method="DoSomething",
                signature="(s)",
                args=["test"],
            )

        assert result["success"] is True
        mock_bus.call_sync.assert_called_once()

    def test_timeout_returns_error(self) -> None:
        with patch("gnome_ui_mcp.desktop.dbus.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.side_effect = RuntimeError("Timeout waiting for reply")

            result = dbus_mod.dbus_call(
                bus_name="org.example",
                object_path="/org/example",
                interface="org.example.Iface",
                method="Slow",
            )

        assert result["success"] is False
        assert "error" in result

    def test_invalid_signature_returns_error(self) -> None:
        result = dbus_mod.dbus_call(
            bus_name="org.example",
            object_path="/org/example",
            interface="org.example.Iface",
            method="Bad",
            signature="(ZZZZ)",
            args=["test"],
        )
        assert result["success"] is False

    def test_result_includes_metadata(self) -> None:
        with patch("gnome_ui_mcp.desktop.dbus.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(s)", ("ok",))

            result = dbus_mod.dbus_call(
                bus_name="org.test",
                object_path="/org/test",
                interface="org.test.Iface",
                method="Ping",
            )

        assert result["bus_name"] == "org.test"
        assert result["method"] == "Ping"
