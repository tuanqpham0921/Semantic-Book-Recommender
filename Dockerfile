FROM python:3.11-slim

WORKDIR /app

COPY ./app /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install gsutil properly via apt
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update && \
    apt-get install -y google-cloud-sdk

EXPOSE 7860

CMD ["sh", "-c", "gsutil cp -r gs://tuanqpham0921_books_rec_data/data /app/data && python main.py"]
