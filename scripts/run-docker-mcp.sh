#!/usr/bin/env bash
set -euo pipefail

IMAGE="${GNOME_UI_MCP_IMAGE:-ghcr.io/asattelmaier/gnome-ui-mcp:latest}"
USER_ID="${MCP_DOCKER_UID:-$(id -u)}"
GROUP_ID="${MCP_DOCKER_GID:-$(id -g)}"

: "${DBUS_SESSION_BUS_ADDRESS:?DBUS_SESSION_BUS_ADDRESS must be set}"
: "${XDG_RUNTIME_DIR:?XDG_RUNTIME_DIR must be set}"
: "${WAYLAND_DISPLAY:?WAYLAND_DISPLAY must be set}"
: "${DISPLAY:?DISPLAY must be set}"
: "${XDG_SESSION_TYPE:?XDG_SESSION_TYPE must be set}"

exec docker run \
  -i \
  --rm \
  --security-opt apparmor=unconfined \
  --network host \
  --user "${USER_ID}:${GROUP_ID}" \
  -e DBUS_SESSION_BUS_ADDRESS \
  -e XDG_RUNTIME_DIR \
  -e WAYLAND_DISPLAY \
  -e DISPLAY \
  -e XDG_SESSION_TYPE \
  -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  "${IMAGE}" \
  "$@"
