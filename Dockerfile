FROM ghcr.io/astral-sh/uv:0.10.10 AS uv

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

LABEL io.modelcontextprotocol.server.name="io.github.asattelmaier/gnome-ui-mcp"

COPY --from=uv /uv /uvx /bin/

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3.12 \
    python3.12-venv \
    python3-gi \
    gir1.2-atspi-2.0 \
    gir1.2-gtk-3.0 \
    gnome-screenshot \
    wl-clipboard \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY scripts ./scripts

RUN chmod +x ./scripts/bootstrap.sh ./scripts/check.sh \
  && ./scripts/bootstrap.sh --no-dev

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"healthcheck","version":"0.1"}}}' \
      | timeout 5 gnome-ui-mcp 2>/dev/null \
      | grep -q '"result"' || exit 1

ENTRYPOINT ["gnome-ui-mcp"]
