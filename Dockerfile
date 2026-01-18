# ==========================================
# Stage 0: Builder
# ==========================================
FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app


ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 1. Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copy the code
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ==========================================
# Stage 1: Final Image
# ==========================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# CONFIGS
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# add venv to Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy venv and code
COPY --from=builder /app/.venv /app/.venv
COPY . /app


RUN groupadd -g 1000 nonroot && \
    useradd -u 1000 -g nonroot -m -s /bin/bash nonroot && \
    chown -R nonroot:nonroot /app

USER nonroot


CMD ["python", "-m", "app.main"]