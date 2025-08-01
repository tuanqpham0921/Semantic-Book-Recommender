# Use an official Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your app code and data
COPY ./app /app
# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Gradio will run on
EXPOSE 7860

# Run the Gradio app
CMD ["sh", "-c", "gsutil cp -r gs://tuanqpham0921_books_rec_data/data /app/data && python main.py"]