# Use Python 3.11 slim image
FROM python:3.11-slim

# Install Node.js and curl for building React frontend and healthcheck
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy LeafletJS assets to frontend public directory for React build
RUN mkdir -p /app/Frontend_Data/frontend/public/leaflet-assets && \
    cp -r /app/LeafletJS/Floorplans /app/Frontend_Data/frontend/public/leaflet-assets/ && \
    cp -r /app/LeafletJS/JSON /app/Frontend_Data/frontend/public/leaflet-assets/ && \
    cp /app/LeafletJS/campus.geojson /app/Frontend_Data/frontend/public/leaflet-assets/ && \
    cp -r /app/LeafletJS/plugins /app/Frontend_Data/frontend/public/leaflet-assets/ && \
    echo "✅ LeafletJS assets copied to frontend public directory"

# Build React frontend
WORKDIR /app/Frontend_Data/frontend

# Clean install to avoid package conflicts
RUN rm -rf node_modules package-lock.json && \
    npm install && \
    npm run build

# Return to app root
WORKDIR /app

# Expose port
EXPOSE 8081

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start Flask app
CMD ["python", "-u", "src/api/app.py"]
