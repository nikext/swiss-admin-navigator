# swiss-law MCP server with the index baked in (ADR-002, ADR-017).
# Build from the repo root (the image needs ingest/eid.py and data/index.sqlite):
#   docker build -f mcp_server/Dockerfile -t swiss-law-mcp .
# mcp_server/Dockerfile.dockerignore whitelists what goes into the context.

FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv

FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS deps
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /src
# The workspace lock needs every member's pyproject; only the server's deps are installed.
COPY pyproject.toml uv.lock ./
COPY ingest/pyproject.toml ingest/
COPY mcp_server/pyproject.toml mcp_server/
COPY agents/navigator/pyproject.toml agents/navigator/
COPY evals/pyproject.toml evals/
RUN uv export --package swiss-nav-mcp --no-dev --frozen --no-hashes --no-emit-workspace \
        -o /requirements.txt \
 && uv venv /venv --python /usr/local/bin/python3 \
 && VIRTUAL_ENV=/venv uv pip install --no-cache -r /requirements.txt --compile-bytecode

FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
LABEL org.opencontainers.image.source="https://github.com/nikext/swiss-admin-navigator" \
      org.opencontainers.image.description="Unofficial swiss-law MCP server (Fedlex). Not legal advice." \
      org.opencontainers.image.licenses="Apache-2.0"
# The official image ships the stdlib without .pyc (42 of 686 modules), and the
# app user can't write them, so every cold start recompiled asyncio, json, email,
# http...: 0.83 s -> 0.61 s for the server's imports in this container (ADR-017).
RUN python -m compileall -q -j0 /usr/local/lib/python3.12 \
 && useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=deps /venv /venv
COPY ingest/__init__.py ingest/eid.py ingest/
COPY mcp_server/*.py mcp_server/
COPY data/index.sqlite /app/index.sqlite
RUN python -m compileall -q ingest mcp_server
ENV PATH=/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    INDEX_PATH=/app/index.sqlite \
    PORT=8080
USER app
EXPOSE 8080
# HTTP on $PORT when K_SERVICE is set (Cloud Run); `--http` makes local `docker run` match.
CMD ["python", "-m", "mcp_server.server", "--http", "--host", "0.0.0.0"]
