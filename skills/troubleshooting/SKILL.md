---
name: troubleshooting
description: Troubleshoots GNOME UI MCP server connection, AT-SPI, and desktop session issues. Trigger this skill when ping, list_applications, or other tools fail, or when the server does not start.
---

## Troubleshooting Wizard

You are acting as a troubleshooting wizard to help the user configure and fix their GNOME UI MCP server setup. When this skill is triggered, follow this diagnostic process:

### Step 1: Find and Read Configuration

Locate and read the MCP configuration file. Search for `.mcp.json` in the workspace or `~/.claude/settings.local.json`.

Check for:

- Incorrect command path or arguments
- Missing environment variables (DBUS_SESSION_BUS_ADDRESS, XDG_RUNTIME_DIR, WAYLAND_DISPLAY)
- Wrong transport setting

### Step 2: Triage Common Errors

#### Error: `AT-SPI desktop is not available`

AT-SPI accessibility is not enabled or the daemon is not running.

1. Enable accessibility: `gsettings set org.gnome.desktop.interface toolkit-accessibility true`
2. Verify the AT-SPI daemon: `ps aux | grep at-spi`
3. Restart the session if needed

#### Error: `GDK display is not available`

The server cannot connect to the display.

1. Verify `DISPLAY` and `WAYLAND_DISPLAY` are set
2. If running in Docker, ensure the Wayland socket is mounted
3. Check `XDG_RUNTIME_DIR` points to the correct directory

#### Error: `D-Bus call failed` or `AccessDenied`

The session bus is not reachable or permissions are restricted.

1. Verify `DBUS_SESSION_BUS_ADDRESS` is set correctly
2. If in a container, ensure the bus socket is mounted
3. Some GNOME Shell introspection APIs require an unsandboxed session

#### Error: `wl-paste not found` or `wl-copy not found`

Clipboard tools need `wl-clipboard` installed.

```sh
sudo apt install wl-clipboard
```

#### Error: `wayland-info not found`

```sh
sudo apt install wayland-utils
```

#### Symptom: Tools return empty results

- The desktop may have no running applications
- AT-SPI may not expose elements for some apps (Electron, web views)
- Try `ping` first to verify basic connectivity
- Use `screenshot` to see the actual desktop state

### Step 3: Run Diagnostic Commands

```sh
# Verify the server starts
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | uv run gnome-ui-mcp

# Check AT-SPI
python3 -c "import gi; gi.require_version('Atspi', '2.0'); from gi.repository import Atspi; Atspi.init(); print(f'Desktop count: {Atspi.get_desktop_count()}')"

# Check environment
echo "DISPLAY=$DISPLAY"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
```

### Step 4: Check GitHub Issues

If the issue is not covered above, search for existing issues:

```sh
gh issue list --repo asattelmaier/gnome-ui-mcp --search "<error snippet>" --state all
```

Or direct the user to https://github.com/asattelmaier/gnome-ui-mcp/issues.
