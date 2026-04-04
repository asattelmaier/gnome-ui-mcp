from __future__ import annotations

import argparse
from collections.abc import Sequence

from .server import run


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
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run(transport=args.transport)


if __name__ == "__main__":
    main()
