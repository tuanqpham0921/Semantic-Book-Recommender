# Makefile for Book Recommender API
.PHONY: help install test test-unit test-integration run dev clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only (fast)"
	@echo "  make test-integration - Run integration tests only (expensive)"
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

# tuanqpham0921/semantic-book-recommender-dev@sha256:...
GCP-dev:
	docker buildx build --platform linux/amd64 -t tuanqpham0921/semantic-book-recommender-dev:latest --push .