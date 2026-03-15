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

## Releasing

Preferred path:

```bash
./scripts/release.sh patch
```

The script updates `pyproject.toml`, `server.json`, and `uv.lock`, refreshes
the local environment, runs `./scripts/check.sh`, creates the release commit,
and adds the annotated tag locally. It does not push.

You can also release an explicit version:

```bash
./scripts/release.sh 0.1.1
```

To preview the next version without changing anything:

```bash
./scripts/release.sh --dry-run patch
```

After the script finishes, push the branch and the tag:

```bash
git push origin main
git push origin v0.1.1
```

Optionally publish a GitHub Release for the same tag.

Pushing a `v*` tag triggers CI and publishes versioned GHCR image tags.
The same tag push also publishes the server metadata to the official MCP Registry.
Pushing `main` updates the `latest` image tag.
