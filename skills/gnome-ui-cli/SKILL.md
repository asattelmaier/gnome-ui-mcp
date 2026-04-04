---
name: gnome-ui-cli
description: Use this skill to run GNOME UI MCP tools from the command line or shell scripts for desktop automation.
---

The `gnome-ui-mcp` CLI lets you automate the GNOME desktop from the terminal.

## Setup

Install and run via uv:

```sh
uv run gnome-ui-mcp
```

Or via Docker:

```sh
./scripts/run-docker-mcp.sh
```

The server communicates over stdio using JSON-RPC (MCP protocol).

## AI Workflow

1. **Discover**: Use `list_applications` and `find_elements` to locate UI targets
2. **Inspect**: Use `accessibility_tree` to understand element hierarchy
3. **Act**: Use `click_element`, `type_text`, `press_key` to interact
4. **Verify**: Use `screenshot` or `assert_element` to confirm results

## Quick Test

Send a ping to verify the server is working:

```sh
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | uv run gnome-ui-mcp
```

## Transport Options

```sh
uv run gnome-ui-mcp                          # stdio (default)
uv run gnome-ui-mcp --transport sse          # Server-Sent Events
uv run gnome-ui-mcp --transport streamable-http  # Streamable HTTP
```

## Environment Requirements

The server requires these environment variables to be set (they are
typically available in a GNOME Wayland session):

- `DBUS_SESSION_BUS_ADDRESS`
- `XDG_RUNTIME_DIR`
- `WAYLAND_DISPLAY`
- `DISPLAY`
- `XDG_SESSION_TYPE`

## MCP Client Configuration

Add to `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "gnome-ui": {
      "command": "uv",
      "args": ["run", "gnome-ui-mcp"]
    }
  }
}
```
