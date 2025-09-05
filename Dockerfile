FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Admin creation script already copied with backend/

# Force rebuild - Version 2.1.1 - CRITICAL FIX - No authentication required
# Rebuild triggered: 2025-09-05 01:40
RUN echo '#!/bin/bash\necho "Starting Sean Picks API v2.1.1 - Public Access - Fixed"\npython create_admin.py\nuvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]