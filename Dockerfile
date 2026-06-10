# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies (specifically ffmpeg which is required for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy python packaging and dependency files first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install the local package SpotiFLAC
RUN pip install --no-cache-dir .

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV XDG_CACHE_HOME=/config

# Create volumes directory structure
RUN mkdir -p /config /downloads

# Expose configurations and downloads volumes
VOLUME ["/config", "/downloads"]

# Command to run the FastAPI application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
