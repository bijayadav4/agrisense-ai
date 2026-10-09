# ========================================================
# AgriSense AI — Backend Production Dockerfile
# ========================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, models, data
COPY backend/ ./backend/
COPY ml_models/ ./ml_models/

WORKDIR /app/backend

ENV PYTHONPATH="/app/backend"
ENV FLASK_ENV="production"
ENV PORT=5000

EXPOSE 5000

# Run with Gunicorn using preloaded app configuration
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
