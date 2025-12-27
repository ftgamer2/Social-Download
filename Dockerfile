# 1. Use a better base image
FROM python:3.10-slim

# 2. Install FFmpeg (CRITICAL STEP - MISSING IN YOUR OLD FILE)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your app code
COPY app.py .

# 5. Create a downloads folder and give it permissions
RUN mkdir -p /app/downloads && chmod 777 /app/downloads

# 6. Environment Variables
ENV PORT=8080
# ⚠️ Warning: You should move this TOKEN to Koyeb Secrets later for safety
ENV BOT_TOKEN=8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU

# 7. Expose the port for Koyeb Health Check
EXPOSE 8080

# 8. Run the app
CMD ["python", "app.py"]
