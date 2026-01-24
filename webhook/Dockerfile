FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the webhook application
COPY main.py .

# Copy the integrations module needed for Databricks
COPY ../src/integrations/__init__.py /app/src/integrations/
COPY ../src/integrations/databricks.py /app/src/integrations/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/')"

# Run the application
CMD ["python", "main.py"]

