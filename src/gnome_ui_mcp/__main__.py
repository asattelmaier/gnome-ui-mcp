from __future__ import annotations

import argparse
from collections.abc import Sequence

from .server import create_server, run
from .tools.categories import ToolCategory

_CATEGORY_VALUES = sorted(category.value for category in ToolCategory)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gnome-ui-mcp",
        description="Run the GNOME UI MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="Transport to expose. stdio is the default and works best for most MCP clients.",
    )
    parser.add_argument(
        "--category",
        dest="categories",
        action="append",
        choices=_CATEGORY_VALUES,
        metavar="NAME",
        help=(
            "Enable only the given tool category (repeatable). When omitted, all "
            f"categories are enabled. Choices: {', '.join(_CATEGORY_VALUES)}."
        ),
    )
    parser.add_argument(
        "--no-category",
        dest="excluded_categories",
        action="append",
        choices=_CATEGORY_VALUES,
        metavar="NAME",
        help="Disable the given tool category (repeatable), starting from all categories.",
    )
    return parser


def _resolve_categories(
    categories: Sequence[str] | None,
    excluded: Sequence[str] | None,
) -> set[ToolCategory] | None:
    """Compute the enabled category set, or ``None`` for the default (all)."""
    if not categories and not excluded:
        return None

    if categories:
        enabled = {ToolCategory(value) for value in categories}
    else:
        enabled = set(ToolCategory)

    for value in excluded or []:
        enabled.discard(ToolCategory(value))

    return enabled


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    enabled = _resolve_categories(args.categories, args.excluded_categories)
    server = create_server(enabled) if enabled is not None else None
    run(transport=args.transport, server=server)


if __name__ == "__main__":
    main()
