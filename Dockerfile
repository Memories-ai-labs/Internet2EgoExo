FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source
COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

# Run with uvicorn
CMD ["uvicorn", "video_searching_agent.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
