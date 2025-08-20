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
    assemble_filters, extract_query_filters, standardized_genre,
    extract_published_year
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
        
        assert result == "Fiction"

    @patch('app.filter_query.client')
    def test_extract_genre_non_fiction(self, mock_client):
        """Test genre extraction for non-fiction"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"genre": "non-fiction"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_genre("I want non-fiction books")
        
        assert result == "Nonfiction"

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


class TestStandardizedGenre:
    """Test cases for the standardized_genre function using regex patterns."""

    def test_basic_fiction_cases(self):
        """Test standard fiction cases."""
        assert standardized_genre("fiction") == "Fiction"
        assert standardized_genre("Fiction") == "Fiction"
        assert standardized_genre("FICTION") == "Fiction"

    def test_basic_nonfiction_cases(self):
        """Test standard non-fiction cases."""
        assert standardized_genre("non-fiction") == "Nonfiction"
        assert standardized_genre("nonfiction")  == "Nonfiction"
        assert standardized_genre("non fiction") == "Nonfiction"
        assert standardized_genre("Non-Fiction") == "Nonfiction"
        assert standardized_genre("NONFICTION")  == "Nonfiction"

    def test_fiction_with_extra_characters(self):
        """Test fiction words with extra characters attached."""
        assert standardized_genre("fiction12") == "Fiction"
        assert standardized_genre("123fiction") == "Fiction"
        assert standardized_genre("science-fiction") == "Fiction"
        assert standardized_genre("historical-fiction") == "Fiction"
        assert standardized_genre("fictionbook") == "Fiction"

        assert standardized_genre("afictionbook") == "afictionbook"
        assert standardized_genre("abcdfictionbook") == "abcdfictionbook"
        assert standardized_genre("non123fiction") == "Nonfiction"

        # anything with a -fiction will be fiction (if it's not a non-fiction)
        assert standardized_genre("abcd-fiction") == "Fiction"
        assert standardized_genre("nonabcd-fiction") == "Fiction"


    def test_nonfiction_with_extra_characters(self):
        """Test non-fiction words with extra characters attached."""
        assert standardized_genre("nonfiction123") == "Nonfiction"
        assert standardized_genre("123nonfiction") == "Nonfiction"
        assert standardized_genre("nonfictiongsf") == "Nonfiction"
        assert standardized_genre("non-fictionbook") == "Nonfiction"

    def test_nonfiction_takes_priority(self):
        """Test that non-fiction is correctly identified even when 'fiction' is also present."""
        assert standardized_genre("non-fiction") == "Nonfiction"
        assert standardized_genre("nonfiction") == "Nonfiction"
        assert standardized_genre("non fiction book") == "Nonfiction"
        
    def test_words_containing_fiction_but_not_fiction(self):
        """Test that words containing 'fiction' but not actually 'fiction' are not matched."""
        # These should not be classified as Fiction because they don't have word boundaries
        assert standardized_genre("confection") == "confection"
        assert standardized_genre("affection") == "affection"
        assert standardized_genre("infection") == "infection"
        assert standardized_genre("sci-fi") == "sci-fi"

    def test_complex_genre_descriptions(self):
        """Test more complex genre descriptions."""
        assert standardized_genre("science fiction adventure") == "Fiction"
        assert standardized_genre("historical non-fiction") == "Nonfiction"
        assert standardized_genre("young adult fiction") == "Fiction"
        assert standardized_genre("business nonfiction") == "Nonfiction"

    def test_edge_cases_with_punctuation(self):
        """Test edge cases with punctuation and special characters."""
        assert standardized_genre("fiction.") == "Fiction"
        assert standardized_genre("fiction!") == "Fiction"
        assert standardized_genre("fiction?") == "Fiction"
        assert standardized_genre("non-fiction.") == "Nonfiction"
        assert standardized_genre("(fiction)") == "Fiction"
        assert standardized_genre("[nonfiction]") == "Nonfiction"

    def test_non_genre_words(self):
        """Test that non-genre words are returned unchanged."""
        assert standardized_genre("mystery") == "mystery"
        assert standardized_genre("romance") == "romance"
        assert standardized_genre("sci-fi") == "sci-fi"
        assert standardized_genre("fantasy") == "fantasy"
        assert standardized_genre("thriller") == "thriller"
        assert standardized_genre("biography") == "biography"

    def test_empty_and_none_cases(self):
        """Test edge cases with empty strings."""
        assert standardized_genre("") == None
        assert standardized_genre("   ") == None

    def test_mixed_case_scenarios(self):
        """Test various case combinations."""
        assert standardized_genre("ScIeNcE-FiCtIoN") == "Fiction"
        assert standardized_genre("NoN-FiCtIoN") == "Nonfiction"
        assert standardized_genre("HISTORICAL FICTION") == "Fiction"
        assert standardized_genre("medical nonfiction") == "Nonfiction"

    def test_multiple_spaces_and_hyphens(self):
        """Test handling of multiple spaces and different hyphen patterns."""
        assert standardized_genre("non  fiction") == "Nonfiction"  # Multiple spaces
        assert standardized_genre("non--fiction") == "Nonfiction"  # Double hyphen (not matched by pattern)
        assert standardized_genre("non_fiction") == "Nonfiction"  # Underscore (not matched by pattern)
        assert standardized_genre("nonsazcfiction") == "nonsazcfiction"  # should not work


    def test_partial_word_matches(self):
        """Test that partial word matches are handled correctly."""
        # These should match because finctional -> fiction
        assert standardized_genre("fictional") == "Fiction"
        assert standardized_genre("nonfictional") == "Nonfiction"
        
        # These SHOULD match because they have proper word boundaries
        assert standardized_genre("fiction-based") == "Fiction"  # Word boundary at start
        assert standardized_genre("pure fiction") == "Fiction"  # Word boundary at end


class TestPublishedYearExtraction:
    """Unit tests for extract_published_year function."""

    @patch('app.filter_query.client')
    def test_published_year_min(self, mock_client):
        """Test extraction of minimum published year."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"published_year_min": 1990, "published_year_max": null, "published_year_exact": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_published_year("Books published after 1990")
        assert result == {"min": 1990, "max": None, "exact": None}

    @patch('app.filter_query.client')
    def test_published_year_max(self, mock_client):
        """Test extraction of maximum published year."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"published_year_min": null, "published_year_max": 2000, "published_year_exact": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_published_year("Books published before 2000")
        assert result == {"min": None, "max": 2000, "exact": None}

    @patch('app.filter_query.client')
    def test_published_year_exact(self, mock_client):
        """Test extraction of exact published year."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"published_year_min": null, "published_year_max": null, "published_year_exact": 2015}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_published_year("Books published in 2015")
        assert result == {"min": None, "max": None, "exact": 2015}

    @patch('app.filter_query.client')
    def test_published_year_range(self, mock_client):
        """Test extraction of published year range."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"published_year_min": 1980, "published_year_max": 1990, "published_year_exact": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_published_year("Books published from 1980 to 1990")
        assert result == {"min": 1980, "max": 1990, "exact": None}

    @patch('app.filter_query.client')
    def test_no_published_year(self, mock_client):
        """Test when no published year is mentioned."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"published_year_min": null, "published_year_max": null, "published_year_exact": null}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_published_year("Books about adventure")

        assert result == {"min": None, "max": None, "exact": None}
