# Makefile for Book Recommender API
.PHONY: help install test test-unit test-integration run dev clean smoke smoke-interactive

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only (fast)"
	@echo "  make test-integration - Run integration tests only (expensive)"
	@echo "  make run          - Start the API server"
	@echo "  make dev          - Start the API server in development mode"
	@echo "  make smoke        - Quick smoke test (starts server + one curl)"
	@echo "  make smoke-interactive - Interactive smoke test (prompts for input)"
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

# Quick smoke test - starts server and tests one endpoint
# Usage: make smoke QUERY="your description here"
# Default: make smoke (uses default query)
QUERY ?= get me books by Stephen King and J.K. Rowling
smoke: 
	@echo "🚀 Quick Smoke Test"
	@echo "Make sure the server is running with: make dev"
	@echo "Testing with query:"
	@echo "  $(QUERY)"
	@echo ""
	curl -X POST "http://localhost:8000/recommend_books" \
		-H "Content-Type: application/json" \
		-d '{"description": "$(QUERY)"}'

# Interactive smoke test - prompts for user input
smoke-interactive:
	@echo "🚀 Interactive Smoke Test"
	@echo "Make sure the server is running with: make dev"
	@echo ""
	@read -p "Enter your book description: " DESCRIPTION; \
	echo "Testing with description: $$DESCRIPTION"; \
	echo ""; \
	curl -X POST "http://localhost:8000/recommend_books" \
		-H "Content-Type: application/json" \
		-d "{\"description\": \"$$DESCRIPTION\"}" \
		| head -c 500; \
	echo ""; \
	echo "✅ Interactive smoke test completed!"