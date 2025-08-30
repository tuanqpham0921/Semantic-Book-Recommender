# Makefile for Book Recommender API
.PHONY: help install test test-unit test-integration run dev clean db-start db-stop db-status db-setup

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
	@echo "  make db-start     - Start PostgreSQL database"
	@echo "  make db-stop      - Stop PostgreSQL database"
	@echo "  make db-status    - Check database status"
	@echo "  make db-setup     - Set up database with data migration"

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
	source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000

# Start the API server with auto-reload for development
dev:
	source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Clean up cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# tuanqpham0921/semantic-book-recommender-dev@sha256:...
GCP-dev:
	docker buildx build --platform linux/amd64 -t tuanqpham0921/semantic-book-recommender-dev:latest --push .

# Database management commands
db-start:
	docker compose up -d postgres
	@echo "PostgreSQL started! Check status with 'make db-status'"

db-stop:
	docker compose stop postgres
	@echo "PostgreSQL stopped"

db-status:
	@echo "Database status:"
	@docker compose ps postgres
	@docker compose exec postgres pg_isready -U postgres 2>/dev/null && echo "✓ Database is ready" || echo "✗ Database not ready"

db-setup:
	@echo "Setting up database with full migration..."
	python loader.py