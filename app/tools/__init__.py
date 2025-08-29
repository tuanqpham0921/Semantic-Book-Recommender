"""
Tools package for the Book Recommendation System

This package contains utility modules for filtering, querying, validation, and vector search operations.
"""

from .filter_df import apply_post_filters, tone_options, filter_categories, genre_options
from .filter_query import assemble_filters, extract_content
from .filter_validation import (
    validate_author_filter, validate_genre_filter,
    validate_min_pages_filter, validate_max_pages_filter,
    validate_keywords_filter, validate_tone_filter,
    validate_published_year_filter
)
from .vector_search import similarity_search_postgres, get_embedding

__all__ = [
    # Filter DataFrame functions
    "apply_post_filters", "tone_options", "filter_categories", "genre_options",
    
    # Filter Query functions
    "assemble_filters", "extract_content",
    
    # Validation functions
    "validate_author_filter", "validate_genre_filter",
    "validate_min_pages_filter", "validate_max_pages_filter",
    "validate_keywords_filter", "validate_tone_filter",
    "validate_published_year_filter",
    
    # Vector Search functions
    "similarity_search_postgres", "get_embedding"
]
