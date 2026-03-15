FROM ghcr.io/astral-sh/uv:0.10.10 AS uv

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY scripts ./scripts

RUN chmod +x ./scripts/bootstrap.sh ./scripts/check.sh \
  && ./scripts/bootstrap.sh --no-dev

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

ENTRYPOINT ["gnome-ui-mcp"]
