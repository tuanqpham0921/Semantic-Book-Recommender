# Use an official Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code and data
COPY . .

# Expose the port Gradio will run on
EXPOSE 7860

# Set environment variables (optional, or use .env)
# ENV OPENAI_API_KEY=your_openai_api_key_here

# Run the Gradio app
CMD ["python", "main.py"]
