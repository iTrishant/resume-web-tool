# Use Python 3.11.8 as specified in runtime.txt
FROM python:3.11.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire services folder
COPY . .

# Expose port (will be overridden by $PORT environment variable)
EXPOSE 8000

# Start the unified FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
