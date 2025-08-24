import pytest
from unittest.mock import Mock
from app.generate_reason import get_response_messages
from app.models import BookRecommendation, FilterSchema
from app.generate_reason import get_book_filter_messages


class TestGetResponseMessages:
    """Test the get_response_messages function"""
    
    def test_get_response_messages_with_valid_filters(self):
        """Test extracting messages from validation logs with filters that changed book counts"""
        # Create a mock BookRecommendationResponse with validation data
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': {
                'num_books_before': 100,
                'num_books_after': 50,
                'message': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
            },
            'applied_genre': {
                'num_books_before': 50,
                'num_books_after': 20,
                'message': 'Applied genre=Fantasy: narrowed 50 → 20 books.'
            },
            'applied_min_pages': {
                'num_books_before': 20,
                'num_books_after': 15,
                'message': 'Applied pages_min=300: narrowed 20 → 15 books.'
            }
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should include all filters that changed book count and have messages
        expected = {
            'applied_author': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.',
            'applied_genre': 'Applied genre=Fantasy: narrowed 50 → 20 books.',
            'applied_min_pages': 'Applied pages_min=300: narrowed 20 → 15 books.'
        }
        assert result == expected
    
    def test_get_response_messages_filters_no_change(self):
        """Test that filters with no book count change are excluded"""
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': {
                'num_books_before': 100,
                'num_books_after': 50,
                'message': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
            },
            'applied_genre': {
                'num_books_before': 50,
                'num_books_after': 50,  # No change - should be excluded
                'message': 'No filtering applied for genre'
            }
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should only include the author filter since genre didn't change book count
        expected = {
            'applied_author': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
        }
        assert result == expected
    
    def test_get_response_messages_empty_messages(self):
        """Test that filters with empty messages are excluded"""
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': {
                'num_books_before': 100,
                'num_books_after': 50,
                'message': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
            },
            'applied_tone': {
                'num_books_before': 50,
                'num_books_after': 40,
                'message': ''  # Empty message - should be excluded
            }
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should only include the author filter since tone has empty message
        expected = {
            'applied_author': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
        }
        assert result == expected
    
    def test_get_response_messages_none_values(self):
        """Test that None validation values are skipped"""
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': {
                'num_books_before': 100,
                'num_books_after': 50,
                'message': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
            },
            'applied_genre': None,  # None value - should be skipped
            'applied_max_pages': None  # None value - should be skipped
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should only include the author filter since others are None
        expected = {
            'applied_author': 'Applied authors=[J.K. Rowling]: narrowed 100 → 50 books.'
        }
        assert result == expected
    
    def test_get_response_messages_empty_case(self):
        """Test with no valid messages (all excluded)"""
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': None,  # None - excluded
            'applied_genre': {
                'num_books_before': 100,
                'num_books_after': 100,  # No change - excluded
                'message': 'No filtering applied'
            },
            'applied_tone': {
                'num_books_before': 100,
                'num_books_after': 90,
                'message': ''  # Empty message - excluded
            }
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should return empty dict since all filters are excluded
        assert result == {}
    
    def test_get_response_messages_all_filter_types(self):
        """Test with all different filter types that should be included"""
        mock_validation = Mock()
        mock_validation.dict.return_value = {
            'applied_author': {
                'num_books_before': 1000,
                'num_books_after': 150,
                'message': 'Applied authors=[Brandon Sanderson]: narrowed 1000 → 150 books.'
            },
            'applied_genre': {
                'num_books_before': 150,
                'num_books_after': 30,
                'message': 'Applied genre=Fantasy: narrowed 150 → 30 books.'
            },
            'applied_min_pages': {
                'num_books_before': 30,
                'num_books_after': 20,
                'message': 'Applied pages_min=300: narrowed 30 → 20 books.'
            },
            'applied_max_pages': {
                'num_books_before': 20,
                'num_books_after': 15,
                'message': 'Applied pages_max=500: narrowed 20 → 15 books.'
            },
            'applied_keywords': {
                'num_books_before': 15,
                'num_books_after': 10,
                'message': 'Applied keywords=[magic, quest]: narrowed 15 → 10 books.'
            }
        }
        
        mock_request = Mock()
        mock_request.validation = mock_validation
        
        result = get_response_messages(mock_request)
        
        # Should include all filters since they all changed book counts and have messages
        assert len(result) == 5
        assert 'applied_author' in result
        assert 'applied_genre' in result
        assert 'applied_min_pages' in result
        assert 'applied_max_pages' in result
        assert 'applied_keywords' in result


class TestGetBookFilterMessages:
    """Test the get_book_filter_messages function with 10 focused tests"""

    def test_author_filter_match(self, sample_books):
        """Test author filter matching"""
        book_data = sample_books.iloc[0].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(author=["George Orwell"])
        result = get_book_filter_messages(book, filters)
        assert "matched_author" in result
        assert result["matched_author"] == f"The book is by {book.authors}, which matches your author filter for {', '.join(filters.author)}."

    def test_pages_min_filter(self, sample_books):
        """Test minimum pages filter"""
        book_data = sample_books.iloc[2].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(pages_min=300)
        result = get_book_filter_messages(book, filters)
        assert "matched_min_pages" in result
        assert result["matched_min_pages"] == f"The book has {book.num_pages} pages, which meets your minimum page count filter of {filters.pages_min}."

    def test_pages_max_filter(self, sample_books):
        """Test maximum pages filter"""
        book_data = sample_books.iloc[5].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(pages_max=200)
        result = get_book_filter_messages(book, filters)
        assert "matched_max_pages" in result
        assert result["matched_max_pages"] == f"The book has {book.num_pages} pages, which meets your maximum page count filter of {filters.pages_max}."

    def test_published_year_min_filter(self, sample_books):
        """Test published year minimum filter"""
        book_data = sample_books.iloc[6].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(published_year={"min": 2000})
        result = get_book_filter_messages(book, filters)
        assert "matched_min_published_year" in result
        assert result["matched_min_published_year"] == f"The book was published in {book.published_year}, which meets your minimum published year filter of {filters.published_year['min']}."

    def test_published_year_max_filter(self, sample_books):
        """Test published year maximum filter"""
        book_data = sample_books.iloc[0].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(published_year={"max": 1950})
        result = get_book_filter_messages(book, filters)
        assert "matched_max_published_year" in result
        assert result["matched_max_published_year"] == f"The book was published in {book.published_year}, which meets your maximum published year filter of {filters.published_year['max']}."

    def test_published_year_exact_filter(self, sample_books):
        """Test published year exact match filter"""
        book_data = sample_books.iloc[8].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(published_year={"exact": 1986})
        result = get_book_filter_messages(book, filters)
        assert "matched_exact_published_year" in result
        assert result["matched_exact_published_year"] == f"The book was published in {book.published_year}, which exactly matches your published year filter of {filters.published_year['exact']}."

    def test_genre_and_children_filter(self, sample_books):
        """Test children's genre filter"""
        book_data = sample_books.iloc[1].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(children=True, genre="Fiction")
        result = get_book_filter_messages(book, filters)
        assert "matched_children" in result
        assert "matched_genre_categories" in result
        assert result["matched_children"] == "You requested Children's books."
        assert result["matched_genre_categories"] == f"The book belongs to the {book.simple_categories} category(ies), which matches your genre Children's Fiction."

    def test_keywords_description_filter(self, sample_books):
        """Test keywords matching in description"""
        book_data = sample_books.iloc[0].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(keywords=["totalitarian"])
        result = get_book_filter_messages(book, filters)
        assert "matched_keywords" in result
        assert result["matched_keywords"] == f"The book's description matches your keywords: {', '.join(filters.keywords)}."

    def test_keywords_title_filter(self, sample_books):
        """Test keywords matching in title"""
        book_data = sample_books.iloc[1].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(keywords=["Harry Potter"])
        result = get_book_filter_messages(book, filters)
        assert "matched_title" in result
        assert result["matched_title"] == f"The book's title matches your keywords: {', '.join(filters.keywords)}."

    def test_tone_filter(self, sample_books):
        """Test tone filter for high fear books"""
        book_data = sample_books.iloc[8].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(tone="fear")
        result = get_book_filter_messages(book, filters)
        assert "matched_tone" in result
        assert result["matched_tone"] == f"The book has a {filters.tone} tone score of {str(getattr(book, filters.tone))[:5]} out of 1.0"

    def test_multiple_filters_combined(self, sample_books):
        """Test multiple filters combined - mixed case"""
        book_data = sample_books.iloc[2].to_dict()
        book = BookRecommendation(**book_data)
        filters = FilterSchema(
            author=["Stephen King"],
            genre="Fiction",
            pages_min=300,
            published_year={"min": 1970, "max": 1980},
            keywords=["horror"],
            tone="fear"
        )
        result = get_book_filter_messages(book, filters)
        assert len(result) == 7
        assert "matched_author" in result
        assert "matched_min_pages" in result
        assert "matched_min_published_year" in result
        assert "matched_max_published_year" in result
        assert "matched_genre_categories" in result
        assert "matched_keywords" in result
        assert "matched_tone" in result

    def test_children_filter_no_genre(self, sample_books):
        """Test children's filter without a specific genre, matching both fiction and nonfiction."""
        book_data = sample_books.iloc[1].to_dict()  # Harry Potter, a Children's Fiction book
        book = BookRecommendation(**book_data)
        filters = FilterSchema(children=True)  # No genre specified
        result = get_book_filter_messages(book, filters)

        assert "matched_children" in result
        assert "matched_genre_categories" in result
        assert result["matched_children"] == "You requested Children's books."
        
        expected_genres = "Children's Fiction, Children's Nonfiction"
        assert result["matched_genre_categories"] == f"The book belongs to the {book.simple_categories} category(ies), which matches your genre {expected_genres}."
