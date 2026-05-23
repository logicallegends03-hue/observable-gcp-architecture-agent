FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose Streamlit default web port (bound to Cloud Run compatible 8080)
EXPOSE 8080

# Run Streamlit server
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
