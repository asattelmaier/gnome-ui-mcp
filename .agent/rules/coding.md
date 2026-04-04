---
trigger: always_on
---

# Instructions

- Use `./scripts/check.sh` to run the full verification suite.
- Use `uv run pytest tests -q` to run all tests.
- Use `uv run pytest path/to/test.py -q` to run a single test file, for example, `uv run pytest tests/mcp_server/test_mcp_context.py -q`.
- Use `uv run ruff check src tests scripts` to run lint checks.
- Use `uv run python scripts/generate_docs.py` when MCP tool definitions or generated docs change.

## Rules for Python

- Do not use `Any`.
- Do not use bare `except:`.
- Do not use `cast(...)`.
- Do not add `# type: ignore` comments.
