FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire tinygrid project for local package installation
COPY pyercot /tinygrid/pyercot
COPY tinygrid /tinygrid/tinygrid
COPY pyproject.toml /tinygrid/

# Install tinygrid and its dependencies
RUN pip install --no-cache-dir /tinygrid/pyercot
RUN pip install --no-cache-dir /tinygrid

# Copy backend requirements and install
COPY examples/demo/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY examples/demo/backend/ .

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
