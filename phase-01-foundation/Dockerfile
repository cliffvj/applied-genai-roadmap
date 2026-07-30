# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.12.13-slim-bookworm
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.0


FROM ${UV_IMAGE} AS uv


FROM ${PYTHON_IMAGE} AS builder

COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

# Install locked runtime dependencies before copying frequently changed
# application source files. This keeps the dependency layer cacheable.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project \
        --no-editable

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install the application itself as a non-editable package.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --locked \
        --no-dev \
        --no-editable


FROM ${PYTHON_IMAGE} AS runtime

ARG APP_VERSION=0.1.0

LABEL org.opencontainers.image.title="Applied GenAI Foundation" \
      org.opencontainers.image.description="FastAPI foundation for Applied GenAI and AI infrastructure engineering" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.authors="Clifford V. Juan" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    TMPDIR=/tmp \    
    APPLIED_GENAI_HOST=0.0.0.0 \
    APPLIED_GENAI_PORT=8000 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_LOG_LEVEL=info

RUN groupadd \
        --gid 10001 \
        appgroup \
    && useradd \
        --uid 10001 \
        --gid appgroup \
        --no-create-home \
        --home-dir /nonexistent \
        --shell /usr/sbin/nologin \
        appuser

WORKDIR /app

COPY --from=builder \
    --chown=appuser:appgroup \
    /app/.venv \
    /app/.venv

USER 10001:10001

EXPOSE 8000

HEALTHCHECK \
    --interval=10s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import json, os, urllib.request; port = os.getenv('UVICORN_PORT', '8000'); response = urllib.request.urlopen(f'http://127.0.0.1:{port}/health/live', timeout=2); payload = json.load(response); raise SystemExit(0 if response.status == 200 and payload.get('status') == 'healthy' else 1)"]

STOPSIGNAL SIGTERM

CMD ["python", "-m", "uvicorn", "applied_genai.main:app"]

# Local deterministic model-service image used by Docker Compose and tests.
FROM runtime AS mock

COPY --chown=appuser:appgroup \
    scripts/mock_model_service.py \
    /app/scripts/

ENV UVICORN_PORT=8001

EXPOSE 8001

HEALTHCHECK \
    --interval=5s \
    --timeout=3s \
    --start-period=5s \
    --retries=5 \
    CMD ["python", "-c", "import json, urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2); payload = json.load(response); raise SystemExit(0 if response.status == 200 and payload.get('status') == 'healthy' else 1)"]

CMD ["python", "-m", "uvicorn", "scripts.mock_model_service:app"]


# Keep the main API image as the Dockerfile's default final target.
FROM runtime AS production