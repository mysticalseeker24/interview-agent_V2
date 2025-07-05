FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8003

# Set work directory
WORKDIR /app

# Install system dependencies (minimal set, no PostgreSQL)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject_json.toml pyproject.toml
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY ./app ./app

# Copy patterns and other data files
COPY ./patterns ./patterns
COPY ./resume-data ./resume-data

# Create data and upload directories
RUN mkdir -p data/resumes data/metadata uploads

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/v1/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main_json:app", "--host", "0.0.0.0", "--port", "8003"]
