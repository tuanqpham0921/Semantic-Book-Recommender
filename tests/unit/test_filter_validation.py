# tests/unit/test_filter_validation.py
import pytest
import pandas as pd
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_validation import (
    validate_author_filter,
    validate_genre_filter, 
    validate_min_pages_filter,
    validate_max_pages_filter,
    validate_keywords_filter,
    validate_tone_filter
)

class TestValidateAuthorFilter:
    """Test cases for validate_author_filter function"""

    def test_successful_single_author_validation(self, sample_books):
        """Test validation passes when all books match single author"""
        # Filter to only Stephen King books
        king_books = sample_books[sample_books['authors'].str.contains('Stephen King')]
        filterValidation = {}
        
        validate_author_filter(king_books, ['Stephen King'], filterValidation)
        
        assert 'applied_author' in filterValidation
        author_val = filterValidation['applied_author']
        assert author_val['applied'] == True
        assert author_val['status'] == 'success'
        assert author_val['num_books_after'] == 3
        assert author_val['filter_value'] == ['Stephen King']
        assert 'error' not in author_val

    def test_successful_multiple_author_validation(self, sample_books):
        """Test validation passes when all books match one of multiple authors"""
        # Filter to Stephen King and J.K. Rowling books
        filtered_books = sample_books[
            sample_books['authors'].str.contains('Stephen King|J.K. Rowling', regex=True)
        ]
        filterValidation = {}
        
        validate_author_filter(filtered_books, ['Stephen King', 'J.K. Rowling'], filterValidation)
        
        author_val = filterValidation['applied_author']
        assert author_val['status'] == 'success'
        assert author_val['num_books_after'] == 5  # 3 Stephen King + 2 J.K. Rowling books
        assert author_val['filter_value'] == ['Stephen King', 'J.K. Rowling']

    def test_failed_author_validation(self, sample_books):
        """Test validation fails when book doesn't match any requested authors"""
        filterValidation = {}
        
        # Try to validate all books against only J.K. Rowling
        validate_author_filter(sample_books, ['J.K. Rowling'], filterValidation)
        
        author_val = filterValidation['applied_author']
        assert author_val['applied'] == True
        assert author_val['status'] == 'failed'
        assert author_val['num_books_after'] == 11  # All 11 books in conftest with new Stephen King book
        assert 'Failed Author Filter' in author_val['error']
        assert 'George Orwell' in author_val['error']  # First book that fails

    def test_empty_books_validation(self):
        """Test validation with empty DataFrame"""
        empty_books = pd.DataFrame(columns=['authors', 'simple_categories', 'num_pages'])
        filterValidation = {}
        
        validate_author_filter(empty_books, ['Stephen King'], filterValidation)
        
        author_val = filterValidation['applied_author']
        assert author_val['status'] == 'success'  # Empty should pass
        assert author_val['num_books_after'] == 0

class TestValidateGenreFilter:
    """Test cases for validate_genre_filter function"""

    def test_successful_genre_validation(self, sample_books):
        """Test validation passes when all books match genre"""
        fiction_books = sample_books[sample_books['simple_categories'] == 'Fiction']
        filterValidation = {}
        
        validate_genre_filter(fiction_books, 'Fiction', filterValidation)
        
        genre_val = filterValidation['applied_genre']
        assert genre_val['applied'] == True
        assert genre_val['status'] == 'success'
        assert genre_val['num_books_after'] == 5  # 5 Fiction books in conftest (added The Talisman)
        assert genre_val['filter_value'] == 'Fiction'

    def test_failed_genre_validation(self, sample_books):
        """Test validation fails when book doesn't match genre"""
        filterValidation = {}
        
        validate_genre_filter(sample_books, 'Fiction', filterValidation)
        
        genre_val = filterValidation['applied_genre']
        assert genre_val['status'] == 'failed'
        assert 'Failed Genre Filter' in genre_val['error']
        assert "Children's Fiction" in genre_val['error']

    def test_children_genre_validation(self, sample_books):
        """Test validation with children's genre"""
        children_books = sample_books[sample_books['simple_categories'] == "Children's Fiction"]
        filterValidation = {}
        
        validate_genre_filter(children_books, "Children's Fiction", filterValidation)
        
        genre_val = filterValidation['applied_genre']
        assert genre_val['status'] == 'success'
        assert genre_val['filter_value'] == "Children's Fiction"

class TestValidateMinPagesFilter:
    """Test cases for validate_min_pages_filter function"""

    def test_successful_min_pages_validation(self, sample_books):
        """Test validation passes when all books meet minimum pages"""
        long_books = sample_books[sample_books['num_pages'] >= 200]
        filterValidation = {}
        
        validate_min_pages_filter(long_books, 200, filterValidation)
        
        min_val = filterValidation['applied_min_pages']
        assert min_val['applied'] == True
        assert min_val['status'] == 'success'
        assert min_val['num_books_after'] == 8  # Books with >= 200 pages in conftest (added The Talisman - 645 pages)
        assert min_val['filter_value'] == 200

    def test_failed_min_pages_validation(self, sample_books):
        """Test validation fails when book has too few pages"""
        filterValidation = {}
        
        validate_min_pages_filter(sample_books, 400, filterValidation)
        
        min_val = filterValidation['applied_min_pages']
        assert min_val['status'] == 'failed'
        assert 'Failed Min Pages Filter' in min_val['error']
        assert '200' in min_val['error']  # First book with insufficient pages (1984 - 200 pages)

    def test_edge_case_exact_min_pages(self, sample_books):
        """Test validation with exact minimum pages"""
        exact_books = sample_books[sample_books['num_pages'] >= 300]
        filterValidation = {}
        
        validate_min_pages_filter(exact_books, 300, filterValidation)
        
        min_val = filterValidation['applied_min_pages']
        assert min_val['status'] == 'success'

class TestValidateMaxPagesFilter:
    """Test cases for validate_max_pages_filter function"""

    def test_successful_max_pages_validation(self, sample_books):
        """Test validation passes when all books are under maximum pages"""
        short_books = sample_books[sample_books['num_pages'] <= 300]
        filterValidation = {}
        
        validate_max_pages_filter(short_books, 300, filterValidation)
        
        max_val = filterValidation['applied_max_pages']
        assert max_val['applied'] == True
        assert max_val['status'] == 'success'
        assert max_val['num_books_after'] == 6  # Books with <= 300 pages in conftest
        assert max_val['filter_value'] == 300

    def test_failed_max_pages_validation(self, sample_books):
        """Test validation fails when book has too many pages"""
        filterValidation = {}
        
        validate_max_pages_filter(sample_books, 200, filterValidation)
        
        max_val = filterValidation['applied_max_pages']
        assert max_val['status'] == 'failed'
        assert 'Failed Max Pages Filter' in max_val['error']
        assert '300' in max_val['error']  # Should mention the failing page count

    def test_edge_case_exact_max_pages(self, sample_books):
        """Test validation with exact maximum pages"""
        exact_books = sample_books[sample_books['num_pages'] <= 1138]  # Updated to match largest book in conftest
        filterValidation = {}
        
        validate_max_pages_filter(exact_books, 1138, filterValidation)
        
        max_val = filterValidation['applied_max_pages']
        assert max_val['status'] == 'success'

class TestFilterValidationIntegration:
    """Integration tests for multiple validation functions"""

    def test_multiple_validations_in_sequence(self, sample_books):
        """Test running multiple validations on the same filterValidation dict"""
        # Filter books step by step
        author_filtered = sample_books[sample_books['authors'].str.contains('Stephen King')]
        genre_filtered = author_filtered[author_filtered['simple_categories'] == 'Fiction']
        page_filtered = genre_filtered[genre_filtered['num_pages'] >= 300]
        
        filterValidation = {}
        
        # Run all validations
        validate_author_filter(author_filtered, ['Stephen King'], filterValidation)
        validate_genre_filter(genre_filtered, 'Fiction', filterValidation)
        validate_min_pages_filter(page_filtered, 300, filterValidation)
        
        # Check all validations passed
        assert filterValidation['applied_author']['status'] == 'success'
        assert filterValidation['applied_genre']['status'] == 'success'
        assert filterValidation['applied_min_pages']['status'] == 'success'
        
        # Check we have all expected keys
        assert len(filterValidation) == 3

    def test_validation_stops_on_first_failure(self, sample_books):
        """Test that validation stops when first invalid book is found"""
        filterValidation = {}
        
        validate_author_filter(sample_books, ['Nonexistent Author'], filterValidation)
        
        author_val = filterValidation['applied_author']
        assert author_val['status'] == 'failed'
        # Should fail on first book (George Orwell - first in conftest)
        assert 'George Orwell' in author_val['error']

class TestValidateKeywordsFilter:
    """Test cases for validate_keywords_filter function"""

    def test_successful_keywords_validation(self, sample_books):
        """Test validation passes when all books contain keywords"""
        # Filter to books that contain 'novel' in description
        novel_books = sample_books[sample_books['description'].str.contains('novel', case=False, na=False)]
        filterValidation = {}
        
        validate_keywords_filter(novel_books, ['novel'], filterValidation)
        
        assert 'applied_keywords' in filterValidation
        keywords_val = filterValidation['applied_keywords']
        assert keywords_val['applied'] == True
        assert keywords_val['status'] == 'success'
        assert keywords_val['filter_value'] == ['novel']
        assert 'error' not in keywords_val

    def test_successful_multiple_keywords_validation(self, sample_books):
        """Test validation passes when books contain any of multiple keywords"""
        # Filter to books that contain either 'wizard' or 'horror'
        keyword_books = sample_books[
            sample_books['description'].str.contains('wizard|horror', case=False, na=False, regex=True)
        ]
        filterValidation = {}
        
        validate_keywords_filter(keyword_books, ['wizard', 'horror'], filterValidation)
        
        keywords_val = filterValidation['applied_keywords']
        assert keywords_val['status'] == 'success'
        assert keywords_val['filter_value'] == ['wizard', 'horror']

    def test_failed_keywords_validation(self, sample_books):
        """Test validation fails when book doesn't contain keywords"""
        filterValidation = {}
        
        # Try to validate all books against a keyword that doesn't exist
        validate_keywords_filter(sample_books, ['nonexistent'], filterValidation)
        
        keywords_val = filterValidation['applied_keywords']
        assert keywords_val['applied'] == True
        assert keywords_val['status'] == 'failed'
        assert 'Failed Keywords Filter' in keywords_val['error']

    def test_empty_keywords_validation(self, sample_books):
        """Test validation with empty keywords list"""
        filterValidation = {}
        
        validate_keywords_filter(sample_books, [], filterValidation)
        
        keywords_val = filterValidation['applied_keywords']
        assert keywords_val['status'] == 'success'  # Empty keywords should pass
        assert keywords_val['filter_value'] == []

    def test_keywords_validation_with_empty_books(self):
        """Test keywords validation with empty DataFrame"""
        empty_books = pd.DataFrame(columns=['description'])
        filterValidation = {}
        
        validate_keywords_filter(empty_books, ['any'], filterValidation)
        
        keywords_val = filterValidation['applied_keywords']
        assert keywords_val['status'] == 'success'  # Empty DataFrame should pass
        assert keywords_val['num_books_after'] == 0

class TestValidateToneFilter:
    """Test cases for validate_tone_filter function"""

    def test_successful_tone_validation(self, sample_books):
        """Test validation passes for tone filter"""
        filterValidation = {}
        
        validate_tone_filter(sample_books, 'joy', filterValidation)
        
        assert 'applied_tone' in filterValidation
        tone_val = filterValidation['applied_tone']
        assert tone_val['applied'] == True
        assert tone_val['status'] == 'success'
        assert tone_val['filter_value'] == 'joy'
        assert tone_val['num_books_after'] == len(sample_books)
        assert 'error' not in tone_val

    def test_tone_validation_with_different_tones(self, sample_books):
        """Test validation works with different tone values"""
        tone_options = ['joy', 'surprise', 'anger', 'fear', 'sadness']
        
        for tone in tone_options:
            filterValidation = {}
            validate_tone_filter(sample_books, tone, filterValidation)
            
            tone_val = filterValidation['applied_tone']
            assert tone_val['status'] == 'success'
            assert tone_val['filter_value'] == tone
            assert tone_val['applied'] == True

    def test_tone_validation_with_empty_books(self):
        """Test tone validation with empty DataFrame"""
        empty_books = pd.DataFrame()
        filterValidation = {}
        
        validate_tone_filter(empty_books, 'joy', filterValidation)
        
        tone_val = filterValidation['applied_tone']
        assert tone_val['status'] == 'success'  # Tone validation always passes
        assert tone_val['num_books_after'] == 0
        assert tone_val['filter_value'] == 'joy'

    def test_tone_validation_always_succeeds(self, sample_books):
        """Test that tone validation always succeeds regardless of content"""
        filterValidation = {}
        
        # Tone validation should always pass since it just confirms sorting was applied
        validate_tone_filter(sample_books, 'invalid_tone', filterValidation)
        
        tone_val = filterValidation['applied_tone']
        assert tone_val['status'] == 'success'
        assert tone_val['filter_value'] == 'invalid_tone'
