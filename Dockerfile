FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Set environment variables directly in Dockerfile
ENV PORT=8080
ENV BOT_TOKEN=8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU

# Expose port
EXPOSE 8080

# Run app
CMD ["python", "app.py"]