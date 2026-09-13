# =========================================================================
#  QMS HUB - Industrial Quality Management System Dockerfile
#  Production Multi-Stage Build: Python 3.12 Slim
# =========================================================================

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --upgrade pip && \
    pip install --user -r requirements.txt

# Final Runtime Image
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/qms/.local/bin:$PATH \
    PORT=8000

# Install runtime libpq for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root industrial application user
RUN useradd -m -u 1000 qms && \
    mkdir -p /app /app/staticfiles /app/media && \
    chown -R qms:qms /app

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder --chown=qms:qms /root/.local /home/qms/.local

# Copy application source code
COPY --chown=qms:qms . .

# Set execution permissions on entrypoint
RUN chmod +x entrypoint.sh

USER qms

EXPOSE 8000

# Liveness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
