# Multi-stage Dockerfile for Python Services
# Optimized for production deployment with security hardening

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# SECURITY: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY . .

# Create directories with proper permissions
RUN mkdir -p /app/audit_logs /app/uploads && \
    chown -R appuser:appuser /app

# SECURITY: Switch to non-root user
USER appuser

# Expose ports for all services
EXPOSE 8001 8002 8003 8004 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run all services
CMD ["python", "main.py"]
