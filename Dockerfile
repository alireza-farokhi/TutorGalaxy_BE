# Use an official Python runtime as a parent image
FROM python:3.10-slim


# Add metadata to the image
LABEL app.name="TuturGalaxyBE" 

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container to /app
WORKDIR /app

# Install minimal required system dependencies for gRPC
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-binary.txt ./

# Install binary packages first
RUN pip install --no-cache-dir -r requirements-binary.txt

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Run gunicorn with 5 workers when the container launches
CMD ["gunicorn", "-w", "5", "--timeout", "300", "-b", "0.0.0.0:80", "wsgi:app"]