# tests/unit/test_search.py
import pytest
import pandas as pd
from unittest.mock import MagicMock
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.search import similarity_search_filtered

@pytest.fixture
def sample_books():
    """Sample books DataFrame for testing"""
    data = [
        {'isbn13': '9780385121675', 'title': 'The Shining', 'authors': 'Stephen King'},
        {'isbn13': '9780307743657', 'title': 'It', 'authors': 'Stephen King'},
        {'isbn13': '9780451524935', 'title': '1984', 'authors': 'George Orwell'},
    ]
    return pd.DataFrame(data)

class TestSimilaritySearchFiltered:
    """Unit tests for similarity_search_filtered function"""

    def test_returns_all_books_when_dataset_small(self, sample_books):
        """When filtered_books <= k, should return all books without calling ChromaDB"""
        mock_db = MagicMock()
        
        result = similarity_search_filtered("test query", sample_books, mock_db, k=5)
        
        assert len(result) == len(sample_books)
        assert result.equals(sample_books)
        mock_db.similarity_search.assert_not_called()

    def test_calls_chromadb_when_dataset_large(self, sample_books):
        """When filtered_books > k, should call ChromaDB"""
        mock_db = MagicMock()
        mock_rec = MagicMock()
        mock_rec.page_content = "9780385121675 <book description>"
        mock_db.similarity_search.return_value = [mock_rec]
        
        result = similarity_search_filtered("test query", sample_books, mock_db, k=1)
        
        mock_db.similarity_search.assert_called_once()

    def test_filters_by_chromadb_results(self, sample_books):
        """Should only return books that match ChromaDB similarity search"""
        mock_db = MagicMock()
        
        # Mock ChromaDB to return only "The Shining"
        mock_rec = MagicMock()
        mock_rec.page_content = "9780385121675 <book description>"
        mock_db.similarity_search.return_value = [mock_rec]
        
        result = similarity_search_filtered("horror", sample_books, mock_db, k=2)
        
        assert len(result) == 1
        assert result.iloc[0]['title'] == 'The Shining'

    def test_respects_k_limit(self, sample_books):
        """Should not return more than k results"""
        mock_db = MagicMock()
        
        # Mock ChromaDB to return all books
        mock_recs = [MagicMock() for _ in range(len(sample_books))]
        for i, (isbn, title) in enumerate(zip(sample_books['isbn13'], sample_books['title'])):
            mock_recs[i].page_content = f'"{isbn}" "{title}"'
        mock_db.similarity_search.return_value = mock_recs
        
        result = similarity_search_filtered("test", sample_books, mock_db, k=2)
        
        assert len(result) <= 2

    def test_handles_no_matches(self, sample_books):
        """Should return empty DataFrame when no ChromaDB results match filtered books"""
        mock_db = MagicMock()
        
        # Mock ChromaDB to return ISBN not in filtered books
        mock_rec = MagicMock()
        mock_rec.page_content = "9999999999999 Nonexistent Book"
        mock_db.similarity_search.return_value = [mock_rec]
        
        result = similarity_search_filtered("test", sample_books, mock_db, k=2)  # k < len(sample_books)
        
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_search_k_calculation(self, sample_books):
        """Should use appropriate search_k for ChromaDB"""
        mock_db = MagicMock()
        mock_db.similarity_search.return_value = []  # Empty results
        
        similarity_search_filtered("test", sample_books, mock_db, k=2)  # k < len(sample_books)
        
        # Should call with search_k = min(2 * 5, 400) = 10
        mock_db.similarity_search.assert_called_with("test", k=10)
