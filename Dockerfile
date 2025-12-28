FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY app.py .

# Environment Variables
ENV PORT=8080
ENV BOT_TOKEN=8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU

# Expose the port
EXPOSE 8080

# Run the app
CMD ["python", "app.py"]