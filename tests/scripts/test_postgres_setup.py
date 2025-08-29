#!/usr/bin/env python3
"""
Test script to verify PostgreSQL setup and vector search functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.database import Base, BookEmbedding
from app.vector_search import get_embedding, similarity_search_postgres
import pandas as pd

def test_database_connection():
    """Test basic database connection"""
    print("Testing database connection...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_pgvector_extension():
    """Test pgvector extension"""
    print("Testing pgvector extension...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Try to create the extension
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
            
            # Test vector operations
            result = connection.execute(text("SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector AS distance"))
            distance = result.fetchone()[0]
            print(f"✓ pgvector extension is working. Test distance: {distance}")
        return True
    except Exception as e:
        print(f"✗ pgvector extension test failed: {e}")
        return False

def test_book_embeddings_table():
    """Test if book_embeddings table exists and has data"""
    print("Testing book_embeddings table...")
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        count = db.query(BookEmbedding).count()
        if count > 0:
            print(f"✓ book_embeddings table has {count} records")
            
            # Test a sample book
            sample_book = db.query(BookEmbedding).first()
            print(f"✓ Sample book: {sample_book.title} by {sample_book.authors}")
        else:
            print("⚠ book_embeddings table is empty. Run migration script first.")
        
        db.close()
        return count > 0
    except Exception as e:
        print(f"✗ book_embeddings table test failed: {e}")
        return False

def test_vector_search():
    """Test vector search functionality"""
    print("Testing vector search...")
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # This will only work if we have some data
        count = db.query(BookEmbedding).count()
        if count > 0:
            # Get first 5 books for testing
            books_df = pd.read_sql(
                "SELECT isbn13 FROM book_embeddings LIMIT 5", 
                engine
            )
            
            results = similarity_search_postgres(
                "fantasy adventure book", 
                books_df, 
                db, 
                k=3
            )
            
            if not results.empty:
                print(f"✓ Vector search returned {len(results)} results")
                print(f"  Top result: {results.iloc[0]['title']}")
            else:
                print("⚠ Vector search returned no results")
        else:
            print("⚠ Cannot test vector search - no data in database")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Vector search test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("PostgreSQL Setup Verification")
    print("=" * 40)
    
    tests = [
        test_database_connection,
        test_pgvector_extension,
        test_book_embeddings_table,
        test_vector_search
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    print("Summary:")
    print(f"Passed: {sum(results)}/{len(results)} tests")
    
    if all(results):
        print("🎉 All tests passed! PostgreSQL setup is working correctly.")
        return 0
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
