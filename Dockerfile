# ---- Base image: a small official Python image ----
FROM python:3.12-slim

# Don't write .pyc files and show logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first: Docker caches this layer,
# so rebuilding after a code change is fast.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/

# Security good practice: don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

# Version label, can be overridden at build time:
#   docker build --build-arg APP_VERSION=1.2.0 .
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

EXPOSE 8000

# Docker checks this to know if the app is healthy
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Gunicorn = production-grade web server (Flask's built-in one is for dev only)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--access-logfile", "-", "app.main:app"]
