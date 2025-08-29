#!/usr/bin/env python3
"""
Test script to verify the API endpoints work with PostgreSQL
"""
import requests
import json
import sys
import os

# Add the parent directory to Python path so we can import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

BASE_URL = "http://localhost:8080"

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"✓ Root endpoint working: {response.json()}")
            return True
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Root endpoint error: {e}")
        return False

def test_reason_query():
    """Test the reason query endpoint"""
    print("Testing reason query endpoint...")
    try:
        payload = {
            "description": "I want a fantasy adventure book with magic and dragons"
        }
        response = requests.post(f"{BASE_URL}/reason_query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Reason query working")
            print(f"  Content: {result['content']}")
            print(f"  Filters: {result['filters']}")
            return True
        else:
            print(f"✗ Reason query failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Reason query error: {e}")
        return False

def test_recommend_books():
    """Test the book recommendation endpoint with PostgreSQL"""
    print("Testing book recommendation endpoint...")
    try:
        payload = {
            "description": "fantasy adventure book",
            "filters": {
                "genre": "Fiction",
                "pages_min": 200
            },
            "content": "magical adventure story"
        }
        response = requests.post(f"{BASE_URL}/recommend_books", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Book recommendation working")
            print(f"  Found {len(result['recommendations'])} recommendations")
            
            if result['recommendations']:
                book = result['recommendations'][0]
                print(f"  Top recommendation: {book['title']} by {book['authors']}")
                print(f"  Rating: {book['average_rating']}")
            
            print(f"  Filters applied: {result['filters']}")
            return True
        else:
            print(f"✗ Book recommendation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Book recommendation error: {e}")
        return False

def main():
    """Run all API tests"""
    print("API Integration Test with PostgreSQL")
    print("=" * 50)
    
    tests = [
        test_root_endpoint,
        test_reason_query,
        test_recommend_books
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
        print("🎉 All API tests passed! PostgreSQL integration is working correctly.")
        return 0
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
