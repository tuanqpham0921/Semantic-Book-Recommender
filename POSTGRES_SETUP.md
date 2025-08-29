# PostgreSQL Integration for Book Recommender

This guide shows how to migrate from Chroma DB to PostgreSQL with pgvector for better scalability and performance.

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- OpenAI API Key

### Quick Setup

1. **Copy environment template:**
   ```bash
   cp .env.template .env
   # Edit .env with your actual OpenAI API key
   ```

2. **Run the setup script:**
   ```bash
   ./setup_postgres.sh
   ```

3. **Start the application:**
   ```bash
   # With Docker:
   docker compose up book-app
   
   # Or locally:
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL:**
   ```bash
   docker compose up -d postgres
   ```

3. **Setup database and extension:**
   ```bash
   docker compose exec postgres psql -U postgres -c "CREATE DATABASE book_recommender;"
   docker compose exec postgres psql -U postgres -d book_recommender -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

4. **Run migration:**
   ```bash
   python tests/scripts/migrate_csv_to_postgres.py
   ```

5. **Test setup:**
   ```bash
   python tests/scripts/test_postgres_setup.py
   ```

## Database Configuration

- **User:** postgres
- **Password:** 1234
- **Port:** 5432
- **Database:** book_recommender
- **Data source:** `data_processing/etc/books.csv`

## Architecture

### Database Schema
The `book_embeddings` table contains:
- **Basic info:** isbn13, title, authors, description, categories
- **Ratings:** published_year, average_rating, num_pages, ratings_count
- **Images:** thumbnail, large_thumbnail
- **Emotions:** anger, disgust, fear, joy, sadness, surprise, neutral
- **Vector:** 1536-dimensional embedding (OpenAI text-embedding-3-small)

### API Changes
No changes to API endpoints - they work exactly the same:
- `POST /reason_query` - Extract filters from natural language
- `POST /recommend_books` - Get book recommendations with vector search

### Performance Benefits
1. **SQL Queries** - More flexible filtering with WHERE clauses
2. **Vector Search** - Native pgvector cosine similarity
3. **Concurrent Access** - Better handling of multiple requests
4. **ACID Compliance** - Data consistency guarantees
5. **Scalability** - Enterprise-grade PostgreSQL features

## Development

### Testing
```bash
# Test database connection and vector search
python tests/scripts/test_postgres_setup.py

# Test API endpoints
curl -X POST "http://localhost:8080/recommend_books" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "fantasy adventure book",
    "filters": {"genre": "Fiction"},
    "content": "magical quest with heroes"
  }'
```

### Migration Status
- ✅ PostgreSQL with pgvector extension
- ✅ Database models and migrations
- ✅ Vector search implementation  
- ✅ API endpoint integration
- ✅ Docker Compose configuration
- ✅ Test scripts and validation

### Database Operations
```bash
# Connect to database
docker compose exec postgres psql -U postgres -d book_recommender

# Check table structure
\d book_embeddings

# Count total books
SELECT COUNT(*) FROM book_embeddings;

# Test vector search
SELECT title, authors FROM book_embeddings ORDER BY embedding <-> '[0.1,0.2,...]'::vector LIMIT 5;
```

## Troubleshooting

### Connection Issues
```bash
# Check PostgreSQL status
docker compose ps

# View logs
docker compose logs postgres

# Test connection
docker compose exec postgres pg_isready -U postgres
```

### Migration Issues
```bash
# Check CSV file
ls -la data_processing/etc/books.csv

# Restart migration (will skip existing books)
python tests/scripts/migrate_csv_to_postgres.py

# Check migration progress
docker compose exec postgres psql -U postgres -d book_recommender -c "SELECT COUNT(*) FROM book_embeddings;"
```

### API Issues
```bash
# Test API is running
curl http://localhost:8080/

# Check application logs
docker compose logs book-app
```

## Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:1234@localhost:5432/book_recommender
POSTGRES_PASSWORD=1234

# Legacy (for backward compatibility)
CHROMA_DB_PATH=./data/chroma_db
BOOKS_PATH=./data/books.parquet
```

The system is now ready for production with PostgreSQL providing better scalability, reliability, and performance than the previous Chroma DB implementation.
