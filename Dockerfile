# --- Stage 1: Build dependencies ---
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (better Docker layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --group prod

# --- Stage 2: Final runtime image ---
FROM python:3.14-slim-bookworm

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Place the virtual environment at the front of the PATH
ENV PATH="/app/.venv/bin:$PATH" \
    DJANGO_ENV=production \
    PYTHONUNBUFFERED=1

# Copy your source code
COPY src/ /app/src/

# Expose Django's default port (change if using uwsgi/gunicorn/uvicorn)
EXPOSE 8000

# Run migrations and start production server (e.g., gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "/app/src", "whatsthedeal_site.wsgi:application"]