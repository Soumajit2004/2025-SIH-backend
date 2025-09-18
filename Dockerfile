# syntax=docker/dockerfile:1.7
# Multi-stage build for FastAPI app using uv (fast dependency installer)

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_LINK_MODE=copy 

# System deps (add build tools only if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (https://github.com/astral-sh/uv)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --yes && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Copy project metadata first for dependency layer caching
COPY pyproject.toml uv.lock* ./

# Create a virtual env via uv and install
RUN uv sync --frozen --no-dev

# Copy application source
COPY app ./app
COPY README.md ./

# Create a non-root user
RUN useradd -u 1001 -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PORT=8000 \
    HOST=0.0.0.0

EXPOSE 8000

# Default command; allow override of workers via env
# Using --host to bind and PORT env from settings; `--reload` is disabled in container
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
