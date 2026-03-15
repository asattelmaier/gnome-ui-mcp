#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "The project environment is missing. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

. .venv/bin/activate

uv sync --active --frozen --check
uv run --active ruff check .
uv run --active ruff format --check .
uv run --active python -m compileall src
uv run --active python -c "import sys; assert sys.version_info[:2] == (3, 12)"
uv run --active python -c "import gi; gi.require_version('Atspi', '2.0'); gi.require_version('Gdk', '3.0'); from gi.repository import Atspi, Gdk"
uv run --active python -c "from gnome_ui_mcp.server import mcp; assert mcp.name == 'gnome-ui-mcp'"
uv run --active gnome-ui-mcp --help >/dev/null
