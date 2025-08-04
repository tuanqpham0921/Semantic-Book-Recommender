# Use an official Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy app code and requirements
COPY . .
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Cloud Run port
EXPOSE 8080

# Run FastAPI with uvicorn on port 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
