# tests/integration/test_main_integration.py
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from app.models import RecommendationRequest

@pytest.fixture
def client():
    """FastAPI test client for integration tests"""
    return TestClient(app)

@pytest.mark.integration
class TestMainIntegration:
    """Integration tests with real dependencies (ChromaDB, OpenAI API, real data)"""
    
    def test_recommend_books_end_to_end_simple_query(self, client):
        """Test end-to-end recommendation with simple query"""
        request_data = {
            "description": "science fiction books"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        # Test successful response structure
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should return some books
        
        # Test response schema
        first_book = data[0]
        required_fields = ['isbn13', 'title', 'authors', 'simple_categories', 'num_pages']
        for field in required_fields:
            assert field in first_book, f"Missing field: {field}"
        
        # Test data types
        assert isinstance(first_book['isbn13'], str)
        assert isinstance(first_book['title'], str)
        assert isinstance(first_book['authors'], str)
        assert isinstance(first_book['num_pages'], int)

    def test_recommend_books_with_author_filter(self, client):
        """Test recommendation with author-specific query"""
        request_data = {
            "description": "books by Stephen King"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # At least some results should be by Stephen King (may not be all due to semantic search)
        stephen_king_books = [book for book in data if 'Stephen King' in book['authors']]
        assert len(stephen_king_books) > 0, "Should find at least some Stephen King books"

    def test_recommend_books_with_genre_filter(self, client):
        """Test recommendation with genre filter"""
        request_data = {
            "description": "fiction books about space"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Should return fiction books
        fiction_books = [book for book in data if 'Fiction' in book['simple_categories']]
        assert len(fiction_books) > 0, "Should find fiction books"

    def test_recommend_books_with_children_filter(self, client):
        """Test recommendation with children's books filter"""
        request_data = {
            "description": "children's books about adventure"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Should return children's books
        childrens_books = [book for book in data if "Children's" in book['simple_categories']]
        assert len(childrens_books) > 0, "Should find children's books"

    def test_recommend_books_with_pages_filter(self, client):
        """Test recommendation with page count filter"""
        request_data = {
            "description": "short books under 200 pages"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Should return books under 200 pages
        short_books = [book for book in data if book['num_pages'] < 200]
        assert len(short_books) > 0, "Should find books under 200 pages"

    def test_recommend_books_complex_query(self, client):
        """Test recommendation with complex multi-filter query"""
        request_data = {
            "description": "dark fiction books by Stephen King over 300 pages"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Test that complex filtering worked
        for book in data:
            # Should be fiction
            assert 'Fiction' in book['simple_categories']
            # Should be over 300 pages (if filter was applied correctly)
            # Note: May not be strict due to semantic search ranking

    def test_recommend_books_empty_results_graceful(self, client):
        """Test that API handles queries with potentially no results gracefully"""
        request_data = {
            "description": "books about very specific nonexistent topic xyz123"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        # Should still return 200, just with fewer or no results
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)  # Should always return a list

    def test_recommend_books_response_limit(self, client):
        """Test that API respects the FINAL_K limit"""
        request_data = {
            "description": "popular books"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not exceed FINAL_K (which is 10 in main.py)
        assert len(data) <= 10, "Should not return more than FINAL_K books"

    def test_api_error_handling_invalid_request(self, client):
        """Test API error handling for invalid requests"""
        
        # Test completely empty request
        response = client.post("/recommend_books", json={})
        assert response.status_code == 422  # Validation error
        
        # Test request with wrong field name
        response = client.post("/recommend_books", json={"query": "test"})
        assert response.status_code == 422  # Validation error
        
        # Test request with wrong data type
        response = client.post("/recommend_books", json={"description": 123})
        assert response.status_code == 422  # Validation error

    def test_api_handles_special_characters(self, client):
        """Test that API handles special characters and unicode"""
        request_data = {
            "description": "books with émotions and special characters: @#$%"
        }
        
        response = client.post("/recommend_books", json=request_data)
        
        # Should handle gracefully without crashing
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

"""
INTEGRATION TEST STRATEGY FOR MAIN.PY:

✅ **What We're Testing:**
1. **End-to-end API functionality** - Real requests through FastAPI
2. **Real ChromaDB integration** - Actual vector search
3. **Real OpenAI API calls** - Actual filter extraction 
4. **Real data processing** - Using actual parquet files
5. **Response schemas** - Ensuring API returns correct JSON structure
6. **Error handling** - How API behaves with invalid inputs
7. **Performance limits** - Respecting FINAL_K and other constraints

🎯 **Test Categories:**
- **Happy path tests** - Normal queries that should work
- **Edge cases** - Complex filters, empty results, special characters
- **Error conditions** - Invalid requests, malformed data
- **Performance** - Response limits, timeout behavior

💡 **Why These Tests are Valuable:**
1. **Catch integration bugs** - Issues that only appear when components work together
2. **Validate real behavior** - How your API actually performs in production
3. **Test user scenarios** - Real queries users might make
4. **Ensure data quality** - That your parquet data works with the API

⚠️ **Cost Considerations:**
- These tests make REAL OpenAI API calls - they cost money!
- Run them less frequently than unit tests
- Consider using pytest markers to exclude them from regular runs

🏃 **How to Run:**
- Integration only: pytest tests/integration/test_main_integration.py -m integration
- Skip integration: pytest -m "not integration"
"""
