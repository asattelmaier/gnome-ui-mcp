# Contributing

## Local setup

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-gi gir1.2-atspi-2.0 gir1.2-gtk-3.0
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

## Releasing

```bash
./scripts/release.sh patch          # bump, check, changelog, commit, tag
git push origin main
git push origin v0.1.4              # triggers the release workflow
```

The release script bumps `pyproject.toml`, `server.json`, and `uv.lock`,
runs `./scripts/check.sh`, generates a changelog from git history, and
creates the commit and annotated tag locally.

Use `minor` or `major` instead of `patch`, or pass an explicit version
like `./scripts/release.sh 0.2.0`. Preview with `--dry-run`.

Pushing the `v*` tag triggers the release workflow which:

- Verifies the build and runs tests
- Builds and pushes the Docker image to GHCR (versioned + `latest`)
- Creates a GitHub Release with an auto-generated changelog
- Publishes the server metadata to the MCP Registry
