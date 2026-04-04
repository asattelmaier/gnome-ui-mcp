#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/release.sh [--dry-run] patch
  ./scripts/release.sh [--dry-run] minor
  ./scripts/release.sh [--dry-run] major
  ./scripts/release.sh [--dry-run] <version>

Examples:
  ./scripts/release.sh patch
  ./scripts/release.sh 0.1.1
  ./scripts/release.sh --dry-run minor
EOF
}

die() {
  echo "$*" >&2
  exit 1
}

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

[[ $# -eq 1 ]] || {
  usage
  exit 1
}

TARGET="$1"

current_version="$(
  python3 - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"

next_version="$(
  python3 - "$current_version" "$TARGET" <<'PY'
import re
import sys

current = sys.argv[1]
target = sys.argv[2]

match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", current)
if not match:
    raise SystemExit(f"Current version is not semantic: {current}")

major, minor, patch = map(int, match.groups())

if target == "patch":
    result = f"{major}.{minor}.{patch + 1}"
elif target == "minor":
    result = f"{major}.{minor + 1}.0"
elif target == "major":
    result = f"{major + 1}.0.0"
elif re.fullmatch(r"\d+\.\d+\.\d+", target):
    result = target
else:
    raise SystemExit(f"Unsupported release target: {target}")

print(result)
PY
)" || die "Failed to determine next version."

[[ "$next_version" != "$current_version" ]] || die "Next version must differ from current version."

worktree_issue=""
git diff --quiet || worktree_issue="Working tree has unstaged changes."
if [[ -z "$worktree_issue" ]]; then
  git diff --cached --quiet || worktree_issue="Working tree has staged changes."
fi
if [[ -z "$worktree_issue" && -n "$(git ls-files --others --exclude-standard)" ]]; then
  worktree_issue="Working tree has untracked files."
fi

tag_issue=""
git rev-parse --verify "refs/tags/v${next_version}" >/dev/null 2>&1 && \
  tag_issue="Tag v${next_version} already exists."

# --- Generate changelog ---
previous_tag="$(git tag --sort=-v:refname | grep '^v' | head -1 || true)"

if [[ -n "$previous_tag" ]]; then
  changelog="$(git log --format="- %s" "${previous_tag}..HEAD" \
    | grep -v "^- Release version" || true)"
else
  changelog="$(git log --format="- %s" \
    | grep -v "^- Release version" || true)"
fi

echo "Current version: $current_version"
echo "Next version:    $next_version"
echo
echo "Changelog:"
echo "$changelog"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo
  [[ -z "$worktree_issue" ]] || echo "Would fail now: $worktree_issue"
  [[ -z "$tag_issue" ]] || echo "Would fail now: $tag_issue"
  echo "Dry run only. No files were changed."
  echo "Would update: pyproject.toml, server.json, marketplace metadata, uv.lock"
  echo "Would run:    uv lock"
  echo "Would run:    ./scripts/bootstrap.sh"
  echo "Would run:    ./scripts/check.sh"
  echo "Would commit: Release version ${next_version}"
  echo "Would tag:    v${next_version}"
  exit 0
fi

[[ -z "$worktree_issue" ]] || die "$worktree_issue"
[[ -z "$tag_issue" ]] || die "$tag_issue"

python3 - "$next_version" <<'PY'
import json
import re
import sys
from pathlib import Path

next_version = sys.argv[1]

pyproject_path = Path("pyproject.toml")
pyproject_text = pyproject_path.read_text(encoding="utf-8")
updated_pyproject, replacements = re.subn(
    r'(?m)^(version = )"[^"]+"$',
    rf'\1"{next_version}"',
    pyproject_text,
    count=1,
)
if replacements != 1:
    raise SystemExit("Failed to update version in pyproject.toml")
pyproject_path.write_text(updated_pyproject, encoding="utf-8")

server_path = Path("server.json")
server = json.loads(server_path.read_text(encoding="utf-8"))
server["version"] = next_version

for package in server.get("packages", []):
    package.pop("version", None)
    identifier = package.get("identifier")
    if isinstance(identifier, str) and ":" in identifier and "@" not in identifier:
        package["identifier"] = f"{identifier.rsplit(':', 1)[0]}:{next_version}"

server_path.write_text(json.dumps(server, indent=2) + "\n", encoding="utf-8")

for metadata_path in (
    Path(".claude-plugin/marketplace.json"),
    Path(".claude-plugin/plugin.json"),
    Path(".github/plugin/plugin.json"),
):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["version"] = next_version
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
PY

uv lock
./scripts/bootstrap.sh
./scripts/check.sh

git add pyproject.toml server.json .claude-plugin .github/plugin uv.lock
git commit -m "Release version ${next_version}

${changelog}"
git tag -a "v${next_version}" -m "Release v${next_version}

${changelog}"

echo
echo "Release prepared."
echo "Commit and tag v${next_version} created locally."
echo
echo "Next steps:"
echo "  git push origin main"
echo "  git push origin v${next_version}"
