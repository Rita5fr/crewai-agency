# =============================================================================
# my_ai_agency - Production Dockerfile
# FastAPI + CrewAI service with Claude and Gemini support
# =============================================================================

# -----------------------------------------------------------------------------
# Base Image
# Using python:3.11-slim for smaller image size while maintaining compatibility
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS base

# -----------------------------------------------------------------------------
# Environment Configuration
# - PYTHONDONTWRITEBYTECODE: Prevents .pyc files (smaller image, no caching needed in containers)
# - PYTHONUNBUFFERED: Ensures logs are sent straight to terminal without buffering
# - PIP_NO_CACHE_DIR: Disables pip cache to reduce image size
# - PIP_DISABLE_PIP_VERSION_CHECK: Speeds up pip operations
# -----------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# -----------------------------------------------------------------------------
# Working Directory
# All subsequent commands will run from this directory
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# System Dependencies
# Install any required system packages, then clean up apt cache
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for some Python packages with native extensions
    gcc \
    # Required for health checks
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# -----------------------------------------------------------------------------
# Python Dependencies
# Copy requirements first to leverage Docker layer caching
# Dependencies are only reinstalled when requirements.txt changes
# -----------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Application Source
# Copy the rest of the application code
# -----------------------------------------------------------------------------
COPY . .

# -----------------------------------------------------------------------------
# Non-Root User (Security Best Practice)
# Running as non-root reduces the attack surface if the container is compromised
# -----------------------------------------------------------------------------
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# -----------------------------------------------------------------------------
# Expose Port
# FastAPI/Uvicorn will listen on this port
# -----------------------------------------------------------------------------
EXPOSE 8000

# -----------------------------------------------------------------------------
# Health Check (Optional but recommended for orchestrators)
# Checks if the API is responding every 30 seconds
# -----------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# -----------------------------------------------------------------------------
# Startup Command
# Run uvicorn with optimized settings for production
# - host 0.0.0.0: Accept connections from any IP (required for Docker)
# - port 8000: Match the exposed port
# -----------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
