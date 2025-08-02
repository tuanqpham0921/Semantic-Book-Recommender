# Use an official Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your app code and data
COPY ./app /app
COPY ./data /app/data
# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Gradio will run on
EXPOSE 7860

# Run the Gradio app
CMD ["python", "main.py"]
