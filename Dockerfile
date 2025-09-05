FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY backend/ .

# Create data directory and copy data files
RUN mkdir -p data
COPY backend/data/*.json data/ 2>/dev/null || :
COPY backend/data/*.db data/ 2>/dev/null || :

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copy admin creation script
COPY backend/create_admin.py .

# Create startup script
RUN echo '#!/bin/bash\npython create_admin.py\nuvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
