#!/bin/bash

echo "Setting up PostgreSQL for Book Recommender..."

# Check if .env exists, if not create from template
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your actual OpenAI API key"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start PostgreSQL container
echo "Starting PostgreSQL with pgvector..."
docker compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 15

# Check if PostgreSQL is accessible
docker compose exec postgres pg_isready -U postgres

if [ $? -eq 0 ]; then
    echo "PostgreSQL is ready!"
    
    # Create the database and enable pgvector extension
    echo "Setting up database and pgvector extension..."
    docker compose exec postgres psql -U postgres -c "CREATE DATABASE book_recommender;" 2>/dev/null || echo "Database already exists"
    docker compose exec postgres psql -U postgres -d book_recommender -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    # Run migration
    echo "Running migration script to load CSV data..."
    python tests/scripts/migrate_csv_to_postgres.py
    
    echo "Setup completed! You can now:"
    echo "1. Start the application with: docker compose up book-app"
    echo "2. Or run locally with: python main.py"
    echo "3. Test the setup with: python tests/scripts/test_postgres_setup.py"
else
    echo "PostgreSQL is not ready. Please check Docker logs:"
    echo "docker compose logs postgres"
fi
