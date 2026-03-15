# Contributing

## Local setup

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-gi gir1.2-atspi-2.0 gir1.2-gtk-3.0 gnome-screenshot
./scripts/bootstrap.sh
```

## Development loop

```bash
uv run --active gnome-ui-mcp
```

## Quality checks

```bash
./scripts/check.sh
```

## Pull requests

1. Create a focused branch.
2. Keep changes scoped and documented.
3. Update the README when the public MCP surface changes.
4. Run `./scripts/check.sh` before opening the PR.
