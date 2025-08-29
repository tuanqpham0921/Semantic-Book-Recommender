#!/usr/bin/env python3
"""
Test the updated PostgreSQL similarity search with filters
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_db
from app.vector_search import similarity_search_postgres

def test_search_with_filters():
    """Test the updated search function with various filters"""
    
    # Get database session
    db = next(get_db())
    
    print("Testing PostgreSQL similarity search with filters...")
    print("=" * 50)
    
    # Test 1: Simple search without filters
    print("\n1. Simple search for 'science fiction':")
    results = similarity_search_postgres("science fiction", {}, db, k=3)
    print(f"Results: {len(results)} books found")
    if not results.empty:
        for _, book in results.head(2).iterrows():
            print(f"  - {book['title']} by {book['authors']}")
    
    # Test 2: Search with author filter
    print("\n2. Search for 'mystery' by authors containing 'King':")
    filters = {"authors": "King"}
    results = similarity_search_postgres("mystery", filters, db, k=3)
    print(f"Results: {len(results)} books found")
    if not results.empty:
        for _, book in results.head(2).iterrows():
            print(f"  - {book['title']} by {book['authors']}")
    
    # Test 3: Search with year range filter
    print("\n3. Search for 'romance' published after 2000:")
    filters = {"published_year": {"min": 2000}}
    results = similarity_search_postgres("romance", filters, db, k=3)
    print(f"Results: {len(results)} books found")
    if not results.empty:
        for _, book in results.head(2).iterrows():
            print(f"  - {book['title']} ({book['published_year']}) by {book['authors']}")
    
    # Test 4: Search with rating filter
    print("\n4. Search for 'thriller' with rating >= 4.0:")
    filters = {"average_rating": {"min": 4.0}}
    results = similarity_search_postgres("thriller", filters, db, k=3)
    print(f"Results: {len(results)} books found")
    if not results.empty:
        for _, book in results.head(2).iterrows():
            print(f"  - {book['title']} (rating: {book['average_rating']}) by {book['authors']}")
    
    db.close()
    print("\n✓ All tests completed successfully!")

if __name__ == "__main__":
    test_search_with_filters()
