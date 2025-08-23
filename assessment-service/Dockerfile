FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for pydub & ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set env var for credentials (but don’t bake JSON into image)
# For local dev only, uncomment and use:
# ENV GOOGLE_APPLICATION_CREDENTIALS="/app/local-bliss-465905-r3-acb77d2aff76.json"

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
