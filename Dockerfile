FROM python:3.11-slim

WORKDIR /app

# Force rebuild by adding timestamp
RUN echo "Build timestamp: $(date)" > /tmp/build_info

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Create data directory with proper permissions (as root)
RUN mkdir -p /tmp && chmod 777 /tmp

USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

CMD ["python", "bot.py"]
