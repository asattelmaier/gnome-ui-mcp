# gnome-ui-mcp

Small MCP server for GNOME Wayland desktop automation.

It exposes GNOME desktop inspection and interaction through AT-SPI for discovery and Mutter RemoteDesktop for input. In practice that means element lookup, activation, typing, screenshots, and wait helpers for the current desktop session.

## Requirements

- Linux host with GNOME Shell on Wayland
- Live local GNOME session on the machine you want to automate
- Session environment available: `DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR`, `WAYLAND_DISPLAY`, `DISPLAY`, `XDG_SESSION_TYPE`

### Docker

- Docker Engine

The container must run on the same machine as the GNOME session and use the session environment plus runtime mounts.

## Docker image

The recommended way to run the server is via the published GHCR image:

```text
ghcr.io/asattelmaier/gnome-ui-mcp:latest
```

`latest` tracks the most recent release. Version tags such as `v0.1.0` publish matching image tags as well.

## Docker setup

Direct `docker run`:

```bash
docker run --rm \
  --security-opt apparmor=unconfined \
  --network host \
  --user "$(id -u):$(id -g)" \
  -e DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
  -e DISPLAY="$DISPLAY" \
  -e XDG_SESSION_TYPE="${XDG_SESSION_TYPE:-wayland}" \
  -v "$XDG_RUNTIME_DIR:$XDG_RUNTIME_DIR" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  ghcr.io/asattelmaier/gnome-ui-mcp:latest
```

`--user "$(id -u):$(id -g)"` is required so the container joins the same user
session as GNOME, D-Bus, and AT-SPI.

Local development via Compose:

This path additionally requires `docker compose`.

1. Copy `.env.example` to `.env`
2. Adjust the values to your session
3. Run:

```bash
docker compose build
docker compose run --rm gnome-ui-mcp
```

## Available transports

The server supports three transports, both locally and in Docker:

- `stdio` (default): recommended for local MCP clients that spawn the server process
- `streamable-http`: recommended for HTTP-based integrations on `http://127.0.0.1:8000/mcp`
- `sse`: available for backwards compatibility on `http://127.0.0.1:8000/sse` with message POSTs to `http://127.0.0.1:8000/messages/`

Examples:

```bash
gnome-ui-mcp
gnome-ui-mcp --transport streamable-http
gnome-ui-mcp --transport sse
```

The same flags can be passed to the Docker image by appending them after the image name:

```bash
docker run ... ghcr.io/asattelmaier/gnome-ui-mcp:latest --transport streamable-http
docker run ... ghcr.io/asattelmaier/gnome-ui-mcp:latest --transport sse
```

## Example MCP client configuration

```json
{
  "mcpServers": {
    "gnome-ui": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--security-opt",
        "apparmor=unconfined",
        "--network",
        "host",
        "--user",
        "1000:1000",
        "-e",
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "-e",
        "XDG_RUNTIME_DIR=/run/user/1000",
        "-e",
        "WAYLAND_DISPLAY=wayland-0",
        "-e",
        "DISPLAY=:0",
        "-e",
        "XDG_SESSION_TYPE=wayland",
        "-v",
        "/run/user/1000:/run/user/1000",
        "-v",
        "/tmp/.X11-unix:/tmp/.X11-unix:ro",
        "ghcr.io/asattelmaier/gnome-ui-mcp:latest"
      ]
    }
  }
}
```

## API Documentation

Complete tool reference available at [https://asattelmaier.github.io/gnome-ui-mcp/](https://asattelmaier.github.io/gnome-ui-mcp/)

## Security

This server can inspect and control the active desktop session. Use it only with trusted MCP clients.
Containerized execution on Ubuntu may require `--security-opt apparmor=unconfined`
so the process can talk to the GNOME session buses.
