# Use an official Python base image
# use Linux/AMD64 for GCP
FROM --platform=linux/amd64 python:3.11-slim

# Set the working directory
WORKDIR /app

# Upgrade pip and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Only Copy what's needed for the app to run
COPY main.py ./
COPY app/ ./app/
COPY data/books.parquet ./data/
COPY data/chroma_db/ ./data/chroma_db/

# Expose Cloud Run port
EXPOSE 8080

# Run FastAPI with uvicorn on port 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]