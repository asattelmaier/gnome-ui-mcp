# Troubleshooting

## General tips

- Run `uv run gnome-ui-mcp --help` to test if the server starts.
- Use `ping` as the first tool call to verify AT-SPI and input backends.
- Check the MCP client logs for connection or serialisation errors.
- Search [GitHub issues](https://github.com/asattelmaier/gnome-ui-mcp/issues)
  for similar problems.

## Debugging

Enable debug logging by setting the `GNOME_UI_MCP_DEBUG` environment
variable:

```json
{
  "mcpServers": {
    "gnome-ui": {
      "command": "uv",
      "args": ["run", "gnome-ui-mcp"],
      "env": {
        "GNOME_UI_MCP_DEBUG": "1"
      }
    }
  }
}
```

## Specific problems

### `AT-SPI desktop is not available`

AT-SPI accessibility is not enabled or the daemon is not running.

1. Enable accessibility:
   ```sh
   gsettings set org.gnome.desktop.interface toolkit-accessibility true
   ```
2. Verify the daemon is running:
   ```sh
   ps aux | grep at-spi
   ```
3. Log out and back in if it was just enabled.

### `GDK display is not available`

The server cannot connect to the display server.

- Verify `DISPLAY` and `WAYLAND_DISPLAY` are set.
- If running in Docker, mount the Wayland and X11 sockets:
  ```sh
  -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}"
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro
  ```
- Ensure `XDG_RUNTIME_DIR` points to the correct directory.

### `D-Bus call failed` or `AccessDenied`

The session bus is not reachable or permissions are restricted.

- Verify `DBUS_SESSION_BUS_ADDRESS` is set:
  ```sh
  echo $DBUS_SESSION_BUS_ADDRESS
  ```
- If running in Docker, mount the D-Bus socket and pass the env var.
- Some GNOME Shell introspection APIs (e.g. `GetWindows`) require an
  unsandboxed session.

### `wl-paste not found` / `wl-copy not found`

Clipboard tools need `wl-clipboard` installed:

```sh
sudo apt install wl-clipboard    # Debian/Ubuntu
sudo dnf install wl-clipboard    # Fedora
```

### `wayland-info not found`

```sh
sudo apt install wayland-utils   # Debian/Ubuntu
sudo dnf install wayland-utils   # Fedora
```

### Tools return empty results

- The desktop may have no running applications.
- AT-SPI may not expose elements for some apps (Electron, certain
  web views).
- Try `ping` first to verify connectivity.
- Use `screenshot` to see the actual desktop state.
- Use `accessibility_tree` to inspect the full hierarchy.

### Docker: `Failed to connect to Mutter Remote Desktop`

The Mutter Remote Desktop session interface is not available inside
Docker by default. The server falls back to AT-SPI for input, which
works for most operations.

If you need Mutter input (e.g. for smooth mouse movement):

```sh
docker run \
  --security-opt apparmor=unconfined \
  --network host \
  -e DBUS_SESSION_BUS_ADDRESS \
  -e XDG_RUNTIME_DIR \
  -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}" \
  ...
```

### Element IDs become stale

After UI changes (window opened, dialog closed, navigation), element
IDs may no longer point to the same element. The server uses locators
to relocate elements automatically when possible. If relocation fails:

1. Run `find_elements` again to get fresh IDs.
2. Use `wait_for_element` to wait for the expected element to appear.

### Clicks don't have any effect

1. Try `activate_element` which uses multiple strategies (action,
   keyboard, mouse fallback).
2. Check if the element is behind another window.
3. Verify `effect_verified` in the response.
4. Use `screenshot` to see the current desktop state.

## Environment checklist

Run this to verify all prerequisites:

```sh
echo "DISPLAY=$DISPLAY"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"

python3 -c "
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi
Atspi.init()
print(f'AT-SPI desktop count: {Atspi.get_desktop_count()}')
d = Atspi.get_desktop(0)
print(f'Applications: {d.get_child_count()}')
"

which wl-paste && echo "wl-clipboard: OK" || echo "wl-clipboard: MISSING"
which wayland-info && echo "wayland-utils: OK" || echo "wayland-utils: MISSING"
```
