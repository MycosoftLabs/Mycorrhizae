# Mycorrhizae Protocol API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    redis>=5.0.0 \
    psycopg2-binary>=2.9.9 \
    asyncpg>=0.29.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    httpx>=0.26.0 \
    python-multipart>=0.0.6 \
    sse-starlette>=1.8.2 \
    cryptography>=41.0.0

# Copy application code
COPY mycorrhizae/ ./mycorrhizae/
COPY services/ ./services/
COPY api/ ./api/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
