# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies
COPY mcp_server/requirements.txt requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY mcp_server/ mcp_server/
COPY configs/ configs/

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/configs
ENV PYTHONUNBUFFERED=1

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Expose MCP endpoint port
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint to run MCP server
# Using fastmcp to expose SSE endpoint
CMD ["fastmcp", "run", "mcp_server/server.py", "--transport", "sse", "--port", "8000"]
