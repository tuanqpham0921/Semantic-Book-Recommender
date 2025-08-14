# tests/test_filter_df.py
import pandas as pd
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_df import apply_pre_filters, apply_post_filters, tone_options

def test_apply_pre_filters_authors_one(sample_books):
    """Test filtering by a single author"""
    filters = {'author': ['George Orwell'], 'pages_max': 350}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)

    assert len(result) == 1
    assert result.iloc[0]['authors'] == 'George Orwell'

def test_apply_pre_filters_authors_two(sample_books):
    """Test filtering by multiple authors"""
    filters = {'author': ['George Orwell', 'J.K. Rowling']}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)

    # Simple length check is often sufficient
    assert len(result) == 3
    
    # Key business logic: all results should match the author filter
    authors_in_result = result['authors'].tolist()
    assert all('George Orwell' in author or 'J.K. Rowling' in author for author in authors_in_result)

def test_apply_pre_filters_authors_none(sample_books):
    """Test filtering with no authors specified"""
    filters = {'pages_min': 350}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)

    # Simple checks for basic functionality
    assert len(result) == 3
    assert all(pages >= 350 for pages in result['num_pages'])

def test_apply_pre_filters_stephen_king_books(sample_books):
    """Test filtering for Stephen King specifically - should get both his books"""
    filters = {'author': ['Stephen King']}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)

    # Should get exactly 2 Stephen King books
    assert len(result) == 2
    
    # All results should be by Stephen King
    assert all('Stephen King' in author for author in result['authors'])
    
    # Should include both his books (regardless of order)
    titles = set(result['title'].tolist())
    expected_stephen_king_books = {'The Shining', 'It'}
    assert titles == expected_stephen_king_books

def test_apply_pre_filters_genre_fiction(sample_books):
    """Test genre filtering works correctly"""
    filters = {'genre': 'Fiction'}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # All results should be Fiction
    assert all(category == 'Fiction' for category in result['simple_categories'])
    
    # Should not include Children's Fiction or Non-Fiction
    categories = set(result['simple_categories'].tolist())
    assert categories == {'Fiction'}

def test_apply_pre_filters_pages_range(sample_books):
    """Test page range filtering"""
    filters = {'pages_min': 200, 'pages_max': 350}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # All books should be within the page range
    pages = result['num_pages'].tolist()
    assert all(200 <= page_count <= 350 for page_count in pages)
    
    # Should exclude books outside the range
    assert len(result) < len(sample_books)  # Should filter out some books

def test_apply_pre_filters_children_fiction(sample_books):
    """Test children's fiction filtering"""
    filters = {'genre': 'Fiction', 'children': True}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # Should get all Children's Fiction books
    assert len(result) == 3  # Both Harry Potter books + Charlie and the Chocolate Factory
    
    # All results should be Children's Fiction
    assert all(category == "Children's Fiction" for category in result['simple_categories'])
    
    # Should include both Harry Potter books and Charlie
    titles = set(result['title'].tolist())
    expected_titles = {
        "Harry Potter and the Sorcerer's Stone", 
        "Harry Potter and the Chamber of Secrets", 
        "Charlie and the Chocolate Factory"
    }
    assert titles == expected_titles

def test_apply_pre_filters_children_non_fiction(sample_books):
    """Test children's non-fiction filtering"""
    filters = {'genre': 'Non-Fiction', 'children': True}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # Should get Children's Non-Fiction books
    assert len(result) == 1  # National Geographic Kids Almanac
    
    # All results should be Children's Non-Fiction
    assert all(category == "Children's Non-Fiction" for category in result['simple_categories'])
    
    # Should be the National Geographic book
    assert result.iloc[0]['title'] == 'National Geographic Kids Almanac 2023'

def test_apply_post_filters_names_flexibility(sample_books):
    """Test name filtering without hardcoding exact results"""
    filters = {'names': ['wizard', 'Harry']}  # Should match Harry Potter books
    result = apply_post_filters(sample_books, filters)
    
    # All results should contain at least one of the names in description
    for _, book in result.iterrows():
        description = book['description'].lower()
        assert 'wizard' in description or 'harry' in description
    
    # Should get both Harry Potter books
    harry_potter_books = result[result['authors'].str.contains('J.K. Rowling')]
    assert len(harry_potter_books) == 2

def test_apply_post_filters_tone_sorting_property(sample_books):
    """Test that tone sorting works correctly without hardcoding order"""
    filters = {'tone': 'fear'}
    result = apply_post_filters(sample_books, filters, k=5)
    
    # Should be sorted by fear in descending order
    fear_values = result['fear'].tolist()
    assert fear_values == sorted(fear_values, reverse=True)
    
    # Highest fear book should be first
    highest_fear_book = result.iloc[0]
    assert highest_fear_book['fear'] == max(sample_books['fear'])

def test_filter_combination_logic(sample_books):
    """Test combining multiple filters works correctly"""
    filters = {
        'author': ['Stephen King'],
        'pages_min': 300,
        'tone': 'fear'
    }
    
    # Apply pre-filters first
    filterValidation = {}
    pre_filtered = apply_pre_filters(sample_books, filters, filterValidation)

    # Should only have Stephen King books >= 300 pages
    assert all('Stephen King' in author for author in pre_filtered['authors'])
    assert all(pages >= 300 for pages in pre_filtered['num_pages'])
    
    # Apply post-filters
    final_result = apply_post_filters(pre_filtered, filters, k=10)
    
    # Should be sorted by fear
    fear_values = final_result['fear'].tolist()
    assert fear_values == sorted(fear_values, reverse=True)

def test_tone_filtering_fear(sample_books):
    """Test filtering and sorting by fear tone"""
    filters = {"tone": "fear"}
    result = apply_post_filters(sample_books, filters, k=3)
    
    # Check that books are sorted by fear in descending order
    fear_values = result["fear"].tolist()
    assert fear_values == sorted(fear_values, reverse=True), "Books should be sorted by fear in descending order"
    
    # the 3 most feared book in this list
    titles = set(result['title'].tolist())
    expected_stephen_king_books = {'The Shining', 'It', '1984'}
    assert titles == expected_stephen_king_books

def test_invalid_tone_ignored(sample_books):
    """Test that invalid tone values are ignored"""
    filters = {"tone": "happiness"}  # Not in tone_options
    result = apply_post_filters(sample_books, filters, k=3)
    
    # Should return first k books without any special sorting
    assert len(result) == 3

def test_all_tone_options_work(sample_books):
    """Test that all tone options from tone_options work correctly"""
    for tone in tone_options:
        filters = {"tone": tone}
        result = apply_post_filters(sample_books, filters, k=3)
        
        # Check that result is sorted by the specified tone
        tone_values = result[tone].tolist()
        assert tone_values == sorted(tone_values, reverse=True), f"Books should be sorted by {tone} in descending order"
        assert len(result) <= 3

def test_tone_with_names_filter(sample_books):
    """Test combining tone filtering with names filtering"""
    filters = {
        "tone": "fear",
        "names": ["wizard", "chocolate"]  # Should match Harry Potter and Charlie
    }
    result = apply_post_filters(sample_books, filters, k=5)
    
    # Should only have books that contain the names
    titles = result["title"].tolist()
    expected_titles = ["Harry Potter and the Sorcerer's Stone", "Harry Potter and the Chamber of Secrets", "Charlie and the Chocolate Factory"]
    assert all(title in expected_titles for title in titles)
    
    # Should be sorted by fear (Harry Potter books have more fear than Charlie)
    assert result.iloc[0]["title"] in ["Harry Potter and the Sorcerer's Stone", "Harry Potter and the Chamber of Secrets"]
    assert result.iloc[-1]["title"] == "Charlie and the Chocolate Factory"  # lowest fear