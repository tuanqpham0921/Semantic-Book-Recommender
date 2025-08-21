import pytest
from unittest.mock import Mock
from app.generate_reason import get_response_messages


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
