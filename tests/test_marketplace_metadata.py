from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _read_json(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_marketplace_metadata_versions_match_project_version() -> None:
    version = _project_version()

    server = _read_json("server.json")
    claude_plugin = _read_json(".claude-plugin/plugin.json")
    claude_marketplace = _read_json(".claude-plugin/marketplace.json")
    github_plugin = _read_json(".github/plugin/plugin.json")

    assert server["version"] == version
    assert claude_plugin["version"] == version
    assert claude_marketplace["version"] == version
    assert github_plugin["version"] == version


def test_plugin_metadata_uses_docker_launcher_script() -> None:
    launcher = "./scripts/run-docker-mcp.sh"

    claude_plugin = _read_json(".claude-plugin/plugin.json")
    github_plugin = _read_json(".github/plugin/plugin.json")

    assert (ROOT / "scripts" / "run-docker-mcp.sh").exists()
    assert claude_plugin["mcpServers"]["gnome-ui"]["command"] == launcher
    assert github_plugin["mcpServers"]["gnome-ui"]["command"] == launcher
