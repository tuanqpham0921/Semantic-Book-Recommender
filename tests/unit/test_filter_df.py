# tests/unit/test_filter_df_updated.py
"""
Updated tests for filter_df.py after moving pre-filters to PostgreSQL
"""
import pandas as pd
import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_df import apply_post_filters, tone_options

@pytest.fixture
def sample_books():
    """Sample books DataFrame for testing post-filters"""
    data = [
        {
            'isbn13': '9780451524935',
            'title': '1984',
            'authors': 'George Orwell',
            'description': 'A dystopian novel about Winston Smith and Big Brother.',
            'joy': 0.1,
            'anger': 0.7,
            'fear': 0.8,
            'sadness': 0.6,
            'surprise': 0.2
        },
        {
            'isbn13': '9780439708180',
            'title': 'Harry Potter and the Sorcerers Stone',
            'authors': 'J.K. Rowling',
            'description': 'A young wizard named Harry Potter discovers his magical heritage.',
            'joy': 0.9,
            'anger': 0.2,
            'fear': 0.3,
            'sadness': 0.1,
            'surprise': 0.8
        },
        {
            'isbn13': '9780385121675',
            'title': 'The Shining',
            'authors': 'Stephen King',
            'description': 'Jack Torrance becomes winter caretaker at the isolated Overlook Hotel.',
            'joy': 0.1,
            'anger': 0.6,
            'fear': 0.9,
            'sadness': 0.4,
            'surprise': 0.7
        },
        {
            'isbn13': '9780307743657',
            'title': 'It',
            'authors': 'Stephen King',
            'description': 'Seven friends face an ancient evil entity known as It.',
            'joy': 0.2,
            'anger': 0.5,
            'fear': 0.95,
            'sadness': 0.7,
            'surprise': 0.6
        }
    ]
    return pd.DataFrame(data)

class TestApplyPostFilters:
    """Test post-filtering functionality"""

    def test_post_filters_no_filters(self, sample_books):
        """Test post-filters with no specific filters applied"""
        filters = {}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        assert len(result) == 4  # Should return all books
        assert isinstance(result, pd.DataFrame)

    def test_post_filters_names_filter(self, sample_books):
        """Test filtering by names/keywords in description"""
        filters = {"names": ["Harry", "wizard"]}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # Should only return Harry Potter book
        assert len(result) == 1
        assert "Harry Potter" in result.iloc[0]['title']

    def test_post_filters_tone_filter_joy(self, sample_books):
        """Test sorting by joy tone"""
        filters = {"tone": "joy"}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # Should return all books, sorted by joy (highest first)
        assert len(result) == 4
        # First book should have highest joy score
        assert result.iloc[0]['title'] == 'Harry Potter and the Sorcerers Stone'  # joy: 0.9

    def test_post_filters_tone_filter_fear(self, sample_books):
        """Test sorting by fear tone"""
        filters = {"tone": "fear"}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # Should return all books, sorted by fear (highest first)
        assert len(result) == 4
        # First book should have highest fear score
        assert result.iloc[0]['title'] == 'It'  # fear: 0.95

    def test_post_filters_combined_filters(self, sample_books):
        """Test combining names and tone filters"""
        filters = {"names": ["evil", "entity"], "tone": "fear"}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # Should only return books with "evil" or "entity" in description, sorted by fear
        assert len(result) == 1
        assert "It" in result.iloc[0]['title']

    def test_post_filters_k_limit(self, sample_books):
        """Test that k parameter limits results"""
        filters = {"tone": "joy"}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=2)
        
        # Should return only top 2 books
        assert len(result) == 2
        # Should be sorted by joy
        assert result.iloc[0]['joy'] >= result.iloc[1]['joy']

    def test_post_filters_invalid_tone(self, sample_books):
        """Test that invalid tone is ignored"""
        filters = {"tone": "invalid_tone"}
        filterValidation = {}
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # Should return all books without sorting by invalid tone
        assert len(result) == 4

    def test_tone_options_constant(self):
        """Test that tone_options contains expected values"""
        expected_tones = ("joy", "surprise", "anger", "fear", "sadness")
        assert tone_options == expected_tones

class TestPostFiltersIntegration:
    """Integration tests for post-filters"""

    def test_empty_dataframe_input(self):
        """Test post-filters with empty DataFrame"""
        empty_df = pd.DataFrame()
        filters = {}  # No filters to avoid KeyError on empty DataFrame
        filterValidation = {}
        
        result = apply_post_filters(empty_df, filters, filterValidation, k=10)
        
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_filter_validation_populated(self, sample_books):
        """Test that filterValidation is populated correctly"""
        filters = {"names": ["Harry"], "tone": "joy"}
        filterValidation = {}
        
        result = apply_post_filters(sample_books, filters, filterValidation, k=10)
        
        # filterValidation should be populated by the validation functions
        assert isinstance(filterValidation, dict)
        # The validation functions should have added entries
        assert len(filterValidation) > 0
