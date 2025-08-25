# Makefile for Book Recommender API
.PHONY: help install test test-unit test-integration run dev clean test-api test-api-batch build-docker-dev build-docker-push-gcp-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only (fast)"
	@echo "  make test-integration - Run integration tests only (expensive)"
	@echo "  make test-api     - Run single API test"
	@echo "  make test-api-batch - Run batch API tests (saves to log file)"
	@echo "  make run          - Start the API server"
	@echo "  make dev          - Start the API server in development mode"
	@echo "  make clean        - Clean up cache files"

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest tests/ -v

# Run only unit tests (fast, no API calls)
test-unit:
	pytest tests/unit/ -v

# Run only integration tests (expensive, real API calls)
test-integration:
	pytest tests/integration/ -v -m integration

# Run single API test
test-api:
	python data_processing/test_api.py --mode single

# Run batch API tests (saves to timestamped log file)
test-api-batch:
	python data_processing/test_api.py --mode batch

# Start the API server
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

# Start the API server with auto-reload for development
dev:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Clean up cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Build for linux/amd64 for GCP deployment
build-docker-dev:
	docker buildx build --platform linux/amd64 -t us-central1-docker.pkg.dev/[YOUR-PROJECT-ID]/[YOUR-REPO-NAME]/semantic-book-recommender-dev:rag_dev --push .

# Alternative: Build and tag for both Docker Hub and Artifact Registry
build-docker-push-gcp-dev:
	docker buildx build --platform linux/amd64 \
		-t tuanqpham0921/semantic-book-recommender-dev:rag_dev \
		-t us-central1-docker.pkg.dev/semantic-book-recommender/bookrec-dev/semantic-book-recommender-dev:rag_dev \
		--push .