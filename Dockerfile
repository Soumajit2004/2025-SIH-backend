# syntax=docker/dockerfile:1.7
# Minimal FastAPI + Hypercorn container (no venv) using:
#  * python:3.13-slim
#  * uv (installed via pip) for fast, locked dependency install
#  * system site-packages (no virtualenv) per user request
#
# Customize port: pass -e PORT=9000 (default 8000)
# Example:
#   docker build -t sih-backend:latest .
#   docker run --rm -e PORT=9000 -p 9000:9000 sih-backend:latest

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_LINK_MODE=copy

# System deps (add build tools only if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip (global) per requirement
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy project metadata first for dependency layer caching
COPY pyproject.toml uv.lock* ./

# Install project dependencies system-wide (no venv). Using pyproject metadata.
# (Note: ignoring uv.lock due to editable project hash constraints in system mode.)
RUN uv pip install --system . --no-deps && \
        uv pip install --system $(uv pip compile --all-extras --no-strip-extras pyproject.toml | awk '{print $1}' | grep -v '^#')

# Copy application source
COPY app ./app
COPY README.md ./

# (Optional) drop privileges - retained root here for simplicity; uncomment below to use non-root
# RUN useradd -u 1001 -m appuser && chown -R appuser:appuser /app
# USER appuser

ENV PORT=8000 HOST=0.0.0.0

EXPOSE ${PORT}

## Runtime command (shell form to allow $PORT substitution)
CMD ["/bin/sh", "-c", "hypercorn --bind ${HOST:-0.0.0.0}:$PORT app.main:app"]
