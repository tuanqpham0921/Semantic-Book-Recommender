# tests/test_filter_df.py
import pandas as pd
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_df import apply_pre_filters, rerank_books_by_keywords_and_tone, tone_options

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
    assert len(result) == 4
    assert all(pages >= 350 for pages in result['num_pages'])

def test_apply_pre_filters_stephen_king_books(sample_books):
    """Test filtering for Stephen King specifically - should get all his books"""
    filters = {'author': ['Stephen King']}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)

    # Should get exactly 3 Stephen King books (including The Talisman)
    assert len(result) == 3
    
    # All results should be by Stephen King
    assert all('Stephen King' in author for author in result['authors'])
    
    # Should include all three of his books (regardless of order)
    titles = set(result['title'].tolist())
    expected_stephen_king_books = {'The Shining', 'It', 'The Talisman'}
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
    filters = {'genre': 'Nonfiction', 'children': True}
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # Should get Children's Non-Fiction books
    assert len(result) == 1  # National Geographic Kids Almanac
    
    # All results should be Children's Non-Fiction
    assert all(category == "Children's Nonfiction" for category in result['simple_categories'])
    
    # Should be the National Geographic book
    assert result.iloc[0]['title'] == 'National Geographic Kids Almanac 2023'


def test_apply_pre_filters_children_only_returns_both_types(sample_books):
    """Test the bug fix: children=True with no genre should return both Fiction and Nonfiction"""
    filters = {'children': True}  # Only children flag, no genre
    filterValidation = {}
    result = apply_pre_filters(sample_books, filters, filterValidation)
    
    # Should get ALL children's books (both Fiction and Nonfiction)
    expected_count = 4  # 3 Children's Fiction + 1 Children's Nonfiction
    assert len(result) == expected_count
    
    # Should include both Children's Fiction and Children's Nonfiction
    categories = set(result['simple_categories'].tolist())
    expected_categories = {"Children's Fiction", "Children's Nonfiction"}
    assert categories == expected_categories
    
    # Verify specific children's books are included
    titles = set(result['title'].tolist())
    expected_titles = {
        "Harry Potter and the Sorcerer's Stone",
        "Harry Potter and the Chamber of Secrets", 
        "Charlie and the Chocolate Factory",
        "National Geographic Kids Almanac 2023"
    }
    assert titles == expected_titles

# ============================================================================
# RERANK_BOOKS_BY_KEYWORDS_AND_TONE TESTS
# ============================================================================

def test_rerank_books_by_keywords_and_tone_empty_input(sample_books):
    """Test that empty input returns empty result"""
    empty_books = sample_books.iloc[0:0]  # Empty DataFrame with same structure
    filters = {"keywords": ["wizard"], "tone": "fear"}
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(empty_books, filters, filterValidation, k=5)
    
    assert len(result) == 0
    assert result.empty


def test_rerank_books_by_keywords_and_tone_no_filters(sample_books):
    """Test that no filters returns first k books in original order"""
    filters = {}
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=3)
    
    assert len(result) == 3
    # Should have rerank_score column with all zeros
    assert 'rerank_score' in result.columns
    assert all(score == 0.0 for score in result['rerank_score'])


def test_rerank_books_by_keywords_and_tone_keyword_scoring(sample_books):
    """Test that keyword scoring works correctly"""
    filters = {"keywords": ["wizard", "magic"]}  # Should boost Harry Potter books
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)

    # make sure that rerank_score is calculated
    assert 'rerank_score' in result.columns
    
    # Find books with keywords in description or title
    books_with_keywords = []
    books_without_keywords = []
    
    for _, book in result.iterrows():
        desc = book['description'].lower()
        title = book['title'].lower()
        has_keyword = any(keyword.lower() in desc or keyword.lower() in title 
                         for keyword in ["wizard", "magic"])
        
        if has_keyword:
            books_with_keywords.append(book['rerank_score'])
        else:
            books_without_keywords.append(book['rerank_score'])
    
    # Books with keywords should generally have higher scores
    if books_with_keywords and books_without_keywords:
        avg_with_keywords = sum(books_with_keywords) / len(books_with_keywords)
        avg_without_keywords = sum(books_without_keywords) / len(books_without_keywords)
        assert avg_with_keywords > avg_without_keywords


def test_rerank_books_by_keywords_and_tone_tone_scoring(sample_books):
    """Test that tone scoring works correctly"""
    filters = {"tone": "fear"}  # Should boost books with high fear scores
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=len(sample_books))
    
    # Books should be sorted by rerank_score (which includes tone scoring)
    rerank_scores = result['rerank_score'].tolist()
    assert rerank_scores == sorted(rerank_scores, reverse=True)
    
    # TODO
    # Books with higher fear scores should generally rank higher
    # Check that correlation between fear score and rank position is negative (higher fear = lower rank number)
    # fear_scores = result['fear'].tolist()
    # ranks = list(range(len(result)))  # 0, 1, 2, ... (lower number = higher rank)
    
    # Calculate simple correlation: books with higher fear should have lower rank numbers
    if len(result) > 1:
        # At least the top book should have a decent fear score
        top_book_fear = result.iloc[0]['fear']
        bottom_book_fear = result.iloc[-1]['fear']
        assert top_book_fear >= bottom_book_fear


def test_rerank_books_by_keywords_and_tone_combined_scoring(sample_books):
    """Test combined keyword and tone scoring"""
    filters = {"keywords": ["wizard"], "tone": "joy"}
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)
    
    # Should be sorted by combined score
    rerank_scores = result['rerank_score'].tolist()
    assert rerank_scores == sorted(rerank_scores, reverse=True)
    
    # Top book should either have keywords or high joy score (or both)
    top_book = result.iloc[0]
    desc = top_book['description'].lower()
    title = top_book['title'].lower()
    has_keyword = 'wizard' in desc or 'wizard' in title
    high_joy = top_book['joy'] > 0.5  # Assuming 0.5 is a reasonable threshold
    
    # Top book should have either keyword match OR some score
    assert has_keyword or high_joy or top_book['rerank_score'] > 0


def test_rerank_books_by_keywords_and_tone_case_insensitive(sample_books):
    """Test that keyword matching is case insensitive"""
    filters_lower = {"keywords": ["wizard"]}
    filters_upper = {"keywords": ["WIZARD"]}
    filters_mixed = {"keywords": ["WiZaRd"]}
    filterValidation = {}
    
    result_lower = rerank_books_by_keywords_and_tone(sample_books, filters_lower, filterValidation, k=5)
    result_upper = rerank_books_by_keywords_and_tone(sample_books, filters_upper, filterValidation, k=5)
    result_mixed = rerank_books_by_keywords_and_tone(sample_books, filters_mixed, filterValidation, k=5)
    
    # All should produce identical rerank scores
    scores_lower = result_lower['rerank_score'].tolist()
    scores_upper = result_upper['rerank_score'].tolist()
    scores_mixed = result_mixed['rerank_score'].tolist()
    
    assert scores_lower == scores_upper == scores_mixed


def test_rerank_books_by_keywords_and_tone_invalid_tone(sample_books):
    """Test that invalid tone values are ignored"""
    filters = {"tone": "happiness"}  # Not in tone_options
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=3)
    
    # Should return books without tone-based scoring (only base score of 0)
    assert len(result) == 3
    assert all(score == 0.0 for score in result['rerank_score'])


def test_rerank_books_by_keywords_and_tone_k_limit(sample_books):
    """Test that k parameter limits results correctly"""
    filters = {"keywords": ["book"]}  # Common word
    filterValidation = {}
    
    for k in [1, 3, 5, 10]:
        result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=k)
        expected_length = min(k, len(sample_books))
        assert len(result) == expected_length


def test_rerank_books_by_keywords_and_tone_multiple_keywords(sample_books):
    """Test scoring with multiple keywords"""
    filters = {"keywords": ["wizard", "magic", "school"]}  # Multiple keywords for Harry Potter
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)
    
    # Books matching multiple keywords should score higher than books matching fewer
    scores = []
    keyword_counts = []
    
    for _, book in result.iterrows():
        desc = book['description'].lower()
        title = book['title'].lower()
        count = sum(1 for keyword in ["wizard", "magic", "school"] 
                   if keyword in desc or keyword in title)
        
        scores.append(book['rerank_score'])
        keyword_counts.append(count)
    
    # If we have books with different keyword counts, higher counts should generally have higher scores
    if len(set(keyword_counts)) > 1:  # If there's variation in keyword matches
        # Find books with most keyword matches
        max_keywords = max(keyword_counts)
        if max_keywords > 0:
            # Books with more keywords should have positive scores
            high_keyword_books = [scores[i] for i, count in enumerate(keyword_counts) if count == max_keywords]
            low_keyword_books = [scores[i] for i, count in enumerate(keyword_counts) if count < max_keywords]
            
            if high_keyword_books and low_keyword_books:
                avg_high = sum(high_keyword_books) / len(high_keyword_books)
                avg_low = sum(low_keyword_books) / len(low_keyword_books)
                assert avg_high >= avg_low


def test_rerank_books_by_keywords_and_tone_title_vs_description(sample_books):
    """Test that title matches get higher weight than description matches"""
    # This test would need specific test data, but we can test the concept
    filters = {"keywords": ["Harry"]}  # Should match Harry Potter in title
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)
    
    # Books with keyword in title should generally rank higher than description-only matches
    title_matches = []
    desc_only_matches = []
    
    for _, book in result.iterrows():
        title = book['title'].lower()
        desc = book['description'].lower()
        
        if 'harry' in title:
            title_matches.append(book['rerank_score'])
        elif 'harry' in desc:
            desc_only_matches.append(book['rerank_score'])
    
    # If we have both types, title matches should generally score higher
    if title_matches and desc_only_matches:
        avg_title = sum(title_matches) / len(title_matches)
        avg_desc = sum(desc_only_matches) / len(desc_only_matches)
        assert avg_title >= avg_desc


def test_rerank_books_by_keywords_and_tone_all_valid_tones(sample_books):
    """Test that all valid tone options work"""
    filterValidation = {}
    
    for tone in tone_options:
        filters = {"tone": tone}
        result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=3)
        
        # Should return results sorted by that tone
        assert len(result) == 3
        tone_scores = result[tone].tolist()
        assert tone_scores == sorted(tone_scores, reverse=True)


def test_rerank_books_by_keywords_and_tone_realistic_scenario(sample_books):
    """Test a realistic re-ranking scenario with known data"""
    # Search for "wizard" with "joy" tone - should boost Harry Potter books
    filters = {"keywords": ["wizard"], "tone": "joy"}
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)
    
    # Verify results are properly sorted by rerank_score
    rerank_scores = result['rerank_score'].tolist()
    assert rerank_scores == sorted(rerank_scores, reverse=True)
    
    # Harry Potter book should rank high due to:
    # 1. "wizard" keyword in description
    # 2. High joy score (0.9)
    harry_potter_books = result[result['title'].str.contains('Harry Potter', na=False)]
    assert len(harry_potter_books) > 0, "Should find Harry Potter books"
    
    # Harry Potter book should have a high rerank score
    hp_score = harry_potter_books.iloc[0]['rerank_score']
    assert hp_score > 2.0, f"Harry Potter should have high rerank score due to keyword+tone match, got {hp_score}"
    
    # The Shining should rank lower despite high fear score (wrong tone)
    shining_books = result[result['title'].str.contains('Shining', na=False)]
    if len(shining_books) > 0:
        shining_score = shining_books.iloc[0]['rerank_score']
        # Shining should score lower than Harry Potter (no keyword match, low joy)
        assert hp_score > shining_score, "Harry Potter should outrank The Shining for wizard+joy search"


def test_rerank_books_by_keywords_and_tone_fear_scenario(sample_books):
    """Test fear-based re-ranking - should favor Stephen King books"""
    filters = {"tone": "fear"}
    filterValidation = {}
    
    result = rerank_books_by_keywords_and_tone(sample_books, filters, filterValidation, k=5)
    
    # Should be sorted by rerank_score
    rerank_scores = result['rerank_score'].tolist()
    assert rerank_scores == sorted(rerank_scores, reverse=True)
    
    # Top books should be high-fear books: The Shining (0.95), 1984 (0.8), It (likely high)
    top_3_titles = [result.iloc[i]['title'] for i in range(min(3, len(result)))]
    
    # The Shining should be in top 3 (highest fear score in sample data)
    assert any('Shining' in title for title in top_3_titles), f"The Shining should be in top 3 for fear search, got: {top_3_titles}"
    
    # Verify The Shining has a high rerank score (should be among the top scorers)
    shining_book = result[result['title'].str.contains('Shining', na=False)]
    if len(shining_book) > 0:
        shining_score = shining_book.iloc[0]['rerank_score']
        max_score = max(result['rerank_score'])
        # Should be within top tier (at least 90% of max score)
        assert shining_score >= max_score * 0.9, f"The Shining should score highly for fear search. Got {shining_score}, max was {max_score}"

