#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

uv venv --allow-existing --python python3 --system-site-packages --no-managed-python
. .venv/bin/activate
uv sync --active --frozen "$@"
