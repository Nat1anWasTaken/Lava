FROM python:3.13.5-alpine AS base

FROM base AS builder

# Install system dependencies needed for building
RUN apk update && apk add --no-cache \
    curl \
    ca-certificates \
    git \
    gcc \
    g++ \
    zlib-dev \
    libffi-dev \
    build-base \
    cmake \
    jpeg-dev

# Install uv using the installer script (works on all platforms including ARMv7)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure uv is in PATH
ENV PATH="/root/.local/bin:$PATH"

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . /app

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM base AS runtime

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install only runtime dependencies
RUN apk update && apk add --no-cache \
    git \
    ca-certificates

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app /app

# Make sure the virtual environment is activated by using the venv's python directly
ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R appuser:appuser /app

USER appuser

# Use the virtual environment's python executable directly
CMD ["/app/.venv/bin/python", "main.py"]
