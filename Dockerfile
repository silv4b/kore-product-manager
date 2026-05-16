# Build stage for frontend assets
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
COPY static ./static
RUN npm install
RUN npm run build

# Build stage for Python dependencies
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-cache

# Final execution stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy the frontend assets (output do Tailwind/Node)
COPY --from=frontend-builder /app/static/css/output.css ./static/css/output.css

# Copy the rest of the application code
COPY . .

# --- CONFIGURAÇÃO DO ENTRYPOINT ---
# Copiamos para o WORKDIR atual (/app) e garantimos permissão
RUN chmod +x /app/entrypoint.sh

# Removi o "RUN collectstatic" daqui.
# Ele agora será executado pelo entrypoint.sh no boot do container.

EXPOSE 8005

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8005", "kore-product-manager.wsgi:application"]