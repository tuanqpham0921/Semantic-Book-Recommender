#!/usr/bin/env python3
"""
Test the modularized vector search functions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_db
from app.vector_search import (
    similarity_search_postgres,
    build_where_clause_and_params,
    get_embedding
)

def test_modular_functions():
    """Test individual modular functions"""
    
    print("Testing modularized vector search functions...")
    print("=" * 50)
    
    # Test 1: Test filter building
    print("\n1. Testing filter building:")
    filters = {
        "authors": "King",
        "published_year": {"min": 2000, "max": 2010},
        "average_rating": {"min": 4.0}
    }
    where_clause, params = build_where_clause_and_params(filters)
    print(f"WHERE clause: {where_clause}")
    print(f"Parameters: {params}")
    
    # Test 2: Test embedding generation
    print("\n2. Testing embedding generation:")
    try:
        embedding = get_embedding("science fiction")
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
    
    # Test 3: Test complete search
    print("\n3. Testing complete search with modular approach:")
    db = next(get_db())
    try:
        results = similarity_search_postgres("mystery thriller", {"authors": "King"}, db, k=2)
        print(f"✓ Search completed, found {len(results)} results")
        if not results.empty:
            print(f"  Sample result: {results.iloc[0]['title']}")
    except Exception as e:
        print(f"✗ Search failed: {e}")
    finally:
        db.close()
    
    print("\n✓ All modular function tests completed!")

if __name__ == "__main__":
    test_modular_functions()
