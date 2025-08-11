# Multi-stage build for production-grade TalentSync Interview Service
FROM python:3.11-slim as builder

# Set environment variables for build optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PORT=8006

# Install runtime dependencies in a single layer
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code (copy requirements first for better caching)
COPY requirements.txt .
COPY app/ ./app/
COPY start_service.py .
COPY upload_datasets_to_pinecone.py .
COPY supabase_migration.sql .
COPY run_supabase_migration.py .
COPY .env.example .env

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R appuser:appuser /app && \
    chmod +x start_service.py upload_datasets_to_pinecone.py run_supabase_migration.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8006

# Health check with extended start period for dataset upload
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -f http://localhost:8006/health || exit 1

# Set default command
CMD ["python", "start_service.py"] 