# Use Python 3.10 slim image
FROM python:3.10-slim

# Install Node.js for building React
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build React frontend
WORKDIR /app/Fanshawe_Navigator-main/frontend
RUN npm install && \
    chmod +x node_modules/.bin/* && \
    mkdir -p public/Fanshawe_Icons && \
    cp -r Fanshawe_Icons/* public/Fanshawe_Icons/ && \
    npm run build

# Return to app root
WORKDIR /app

# Expose port
EXPOSE 8081

# Start Flask app (CORREÇÃO: main.py → src/api/app.py)
CMD ["python", "src/api/app.py"]
