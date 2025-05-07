FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies (without Playwright)
RUN pip install --no-cache-dir -r requirements.txt
RUN crawl4ai-setup
# Copy application code
COPY simple_api.py .
COPY app.py .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "simple_api:app", "--host", "0.0.0.0", "--port", "8000"]
