# tests/unit/test_filter_query_unit.py
import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_query import (
    extract_tone, extract_pages, extract_genre, 
    extract_children, extract_names, extract_authors,
    assemble_filters, extract_query_filters
)

class TestFilterQueryMocked:
    """Test the logic around LLM calls by mocking OpenAI API responses"""
    
    @patch('app.filter_query.client')
    def test_extract_tone_with_mock(self, mock_client):
        """Test tone extraction logic by mocking OpenAI response"""
        # Arrange: Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"tone": "somber"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        # Act
        result = extract_tone("I want a somber book about loss")
        
        # Assert
        assert result == "somber"
        mock_client.chat.completions.create.assert_called_once()
        
    @patch('app.filter_query.client')
    def test_extract_tone_null_response(self, mock_client):
        """Test when LLM returns null for tone"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"tone": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_tone("I want a book about cooking")
        
        assert result is None

    @patch('app.filter_query.client')
    def test_extract_pages_with_mock(self, mock_client):
        """Test page extraction logic"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"pages_min": 200, "pages_max": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_pages("I want a book with at least 200 pages")
        
        assert result == {"pages_min": 200, "pages_max": None}

    @patch('app.filter_query.client')
    def test_extract_children_true(self, mock_client):
        """Test children flag extraction"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"children": true}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_children("I want children's books")
        
        assert result is True

    @patch('app.filter_query.client')
    def test_extract_children_false(self, mock_client):
        """Test children flag returns false for adult books"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"children": false}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_children("I want adult fiction")
        
        assert result is False

    @patch('app.filter_query.client')
    def test_extract_names_with_mock(self, mock_client):
        """Test name extraction logic"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"names": ["New York", "Mars"]}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_names("Books set in New York or Mars")
        
        assert result == ["New York", "Mars"]

    @patch('app.filter_query.client')
    def test_extract_authors_with_mock(self, mock_client):
        """Test author extraction logic"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"names": ["J.K. Rowling", "Stephen King"]}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_authors("Books by J.K. Rowling and Stephen King")
        
        assert result == ["J.K. Rowling", "Stephen King"]

    @patch('app.filter_query.client')
    def test_extract_genre_fiction(self, mock_client):
        """Test genre extraction for fiction"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"genre": "fiction"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_genre("I want fiction books")
        
        assert result == "fiction"

    @patch('app.filter_query.client')
    def test_extract_genre_non_fiction(self, mock_client):
        """Test genre extraction for non-fiction"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"genre": "non-fiction"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_genre("I want non-fiction books")
        
        assert result == "non-fiction"

    def test_assemble_filters_handles_empty_extractions(self):
        """Test that assemble_filters handles empty/null extractions correctly"""
        with patch('app.filter_query.extract_tone', return_value=None):
            with patch('app.filter_query.extract_pages', return_value={"pages_min": None, "pages_max": None}):
                with patch('app.filter_query.extract_genre', return_value=None):
                    with patch('app.filter_query.extract_children', return_value=False):
                        with patch('app.filter_query.extract_names', return_value=[]):
                            with patch('app.filter_query.extract_authors', return_value=[]):
                                
                                result = assemble_filters("just a simple query")
                                
                                # Should return empty dict when nothing is extracted
                                assert result == {}

    def test_assemble_filters_with_values(self):
        """Test assemble_filters with actual extracted values"""
        with patch('app.filter_query.extract_tone', return_value="dark"):
            with patch('app.filter_query.extract_pages', return_value={"pages_min": 100, "pages_max": 300}):
                with patch('app.filter_query.extract_genre', return_value="fiction"):
                    with patch('app.filter_query.extract_children', return_value=True):
                        with patch('app.filter_query.extract_names', return_value=["London"]):
                            with patch('app.filter_query.extract_authors', return_value=["George Orwell"]):
                                
                                result = assemble_filters("dark fiction by George Orwell set in London")
                                
                                expected = {
                                    "tone": "dark",
                                    "pages_min": 100,
                                    "pages_max": 300,
                                    "genre": "fiction",
                                    "children": True,
                                    "names": ["London"],
                                    "author": ["George Orwell"]
                                }
                                assert result == expected

    def test_extract_query_filters_structure(self):
        """Test that extract_query_filters returns expected structure"""
        with patch('app.filter_query.assemble_filters', return_value={"tone": "happy"}):
            with patch('app.filter_query.extract_content', return_value="test content"):
                
                result = extract_query_filters("test query")
                
                # Test structure
                assert "query" in result
                assert "content" in result  
                assert "filters" in result
                assert result["query"] == "test query"
                assert result["content"] == "test content"
                assert result["filters"] == {"tone": "happy"}

    def test_extract_query_filters_empty_filters(self):
        """Test extract_query_filters with no filters extracted"""
        with patch('app.filter_query.assemble_filters', return_value={}):
            with patch('app.filter_query.extract_content', return_value="simple content"):
                
                result = extract_query_filters("simple query")
                
                assert result["filters"] is None  # Should be None when filters dict is empty

    @patch('app.filter_query.client')
    def test_json_parse_error_handling(self, mock_client):
        """Test error handling when OpenAI returns invalid JSON"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'invalid json{'
        mock_client.chat.completions.create.return_value = mock_response
        
        # Should raise an exception
        with pytest.raises(json.JSONDecodeError):
            extract_tone("test query")
