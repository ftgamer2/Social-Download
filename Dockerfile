# 1. Use a better base image with FFmpeg pre-installed
FROM python:3.10-slim

# 2. Install system dependencies (FFmpeg and necessary libraries)
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Copy requirements first for better caching
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY app.py .

# 6. Create necessary directories
RUN mkdir -p /app/downloads /tmp/yt-dlp && \
    chmod 777 /app/downloads /tmp/yt-dlp

# 7. Environment Variables
ENV PORT=8080
ENV BOT_TOKEN=8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

# 8. Expose port
EXPOSE 8080

# 9. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 10. Run the application
CMD ["python", "app.py"]