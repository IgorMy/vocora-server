# Debian slim instead of Alpine: ctranslate2 and onnxruntime (faster-whisper)
# publish no wheels for musl, so they can't be installed on Alpine
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first, in their own layer: rebuilt only when the lock file changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

RUN useradd --create-home --uid 1000 vocora \
    && mkdir -p data/recordings data/models \
    && chown -R vocora:vocora data
USER vocora

EXPOSE 8000

# Listens on all interfaces; the compose file decides which host port maps to it
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
