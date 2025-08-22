import pandas as pd
import logging

from app.filter_validation import (
    validate_author_filter, validate_genre_filter,
    validate_min_pages_filter, validate_max_pages_filter,
    validate_keywords_filter, validate_tone_filter,
    validate_published_year_filter
)

# Get the logger (same configuration as main.py)
logger = logging.getLogger(__name__)

filter_categories = ("tone", "pages_max", "pages_min", "genre", "children", "keywords")
genre_options = ("Fiction", "Nonfiction", "Children's Fiction", "Children's Nonfiction")
tone_options = ("joy", "surprise", "anger", "fear", "sadness")

# perform the pre filters like Authors, Genre, and Pages
def apply_pre_filters(books: pd.DataFrame, filters: dict, filterValidation: dict) -> pd.DataFrame:
    # get the authors filters first
    if "author" in filters and filters["author"] is not None:
        logger.info("APPLYING authors filter")
        authors = filters["author"]

        len_books_before = len(books)
        # Filter books where any of the specified authors appears in the authors field
        author_mask = books["authors"].str.contains('|'.join(authors), case=False, na=False, regex=True)
        books = books[author_mask]
        
        # now we validate author filtering
        validate_author_filter(books, authors, filterValidation, len_books_before)

    # get the Fiction/Nonfiction genre first
    if "genre" in filters and filters["genre"] in ["Fiction", "Nonfiction"]:
        logger.info("APPLYING genre filter")
        genre = filters["genre"]
        if "children" in filters and filters["children"]:
            genre = "Children's " + genre
        
        len_books_before = len(books)
        books = books[books["simple_categories"] == genre]

        # now we validate genre filtering
        validate_genre_filter(books, genre, filterValidation, len_books_before)

    # min and max filter is last
    if "pages_min" in filters and filters["pages_min"] is not None:
        logger.info("APPLYING pages_min filter")
        len_books_before = len(books)
        books = books[books["num_pages"] >= filters["pages_min"]]
        logger.info(f"Has {len(books)} books after pages_min: {filters['pages_min']} filter.")

        validate_min_pages_filter(books, filters["pages_min"], filterValidation, len_books_before)

    if "pages_max" in filters and filters["pages_max"] is not None:
        logger.info("APPLYING pages_max filter")
        len_books_before = len(books)
        books = books[books["num_pages"] <= filters["pages_max"]]
        logger.info(f"Has {len(books)} books after pages_max: {filters['pages_max']} filter.")

        validate_max_pages_filter(books, filters["pages_max"], filterValidation, len_books_before)

    if "published_year" in filters and filters["published_year"] is not None:
        logger.info("APPLYING published_year filter")
        published_year = filters["published_year"]

        len_books_before = len(books)
        # Check for exact year first (takes priority)
        if published_year.get("exact") is not None:
            books = books[books["published_year"] == published_year["exact"]]
        
        # Apply min/max filters if exact is not specified
        if published_year.get("min") is not None:
            books = books[books["published_year"] >= published_year["min"]]
        if published_year.get("max") is not None:
            books = books[books["published_year"] <= published_year["max"]]

        validate_published_year_filter(books, published_year, filterValidation, len_books_before)

    return books

# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------

def rerank_books_by_keywords_and_tone(books: pd.DataFrame, filters: dict, filterValidation: dict, k = 10) -> pd.DataFrame:
    """
    Advanced re-ranking system for book recommendations based on keywords and tone.
    
    Args:
        books: DataFrame of candidate books
        filters: Dictionary containing "keywords" (keywords) and 'tone' filters
        k: Number of top books to return
    
    Returns:
        DataFrame of re-ranked books
    """
    if books.empty:
        return books
    
    # Create a copy to avoid modifying original
    ranked_books = books.copy()
    ranked_books['rerank_score'] = 0.0
    
    # 1. KEYWORD RELEVANCE SCORING
    if "keywords" in filters and filters["keywords"]:
        keywords = filters["keywords"]
        logger.info(f"Re-ranking based on keywords: {keywords}")
        
        for keyword in keywords:
            # Score based on keyword frequency in description
            keyword_freq = ranked_books['description'].str.count(keyword, case=False).fillna(0)
            
            # Score based on keyword in title (higher weight)
            title_match = ranked_books['title'].str.contains(keyword, case=False, na=False).astype(int) * 2
            
            # Combine keyword scores (normalized)
            max_freq = keyword_freq.max() if keyword_freq.max() > 0 else 1
            keyword_score = (keyword_freq / max_freq) + title_match
            
            ranked_books['rerank_score'] += keyword_score
    
    # 2. TONE-BASED SCORING
    if "tone" in filters and filters["tone"] in tone_options:
        target_tone = filters["tone"]
        logger.info(f"Re-ranking based on tone: {target_tone}")
        
        # Primary tone score (main factor)
        tone_score = ranked_books[target_tone].fillna(0)
        
        # Tone purity bonus (books that are strongly this tone vs mixed)
        other_tones = [t for t in tone_options if t != target_tone]
        other_tone_avg = ranked_books[other_tones].mean(axis=1).fillna(0)
        tone_purity = tone_score - (other_tone_avg * 0.3)  # Penalty for mixed tones
        
        # Combine tone scores (weight: 60% pure tone, 40% tone purity)
        combined_tone_score = (0.6 * tone_score) + (0.4 * tone_purity.clip(lower=0))
        
        ranked_books['rerank_score'] += combined_tone_score * 2  # Higher weight for tone
    
    # Sort by rerank_score (descending)
    ranked_books = ranked_books.sort_values('rerank_score', ascending=False)
    
    # Log top scoring factors for debugging
    if not ranked_books.empty:
        top_book = ranked_books.iloc[0]
        logger.info(f"Top book: '{top_book['title']}' with rerank_score: {top_book['rerank_score']:.3f}")
    
    # Remove the rerank_score column before returning
    # result = ranked_books.head(k).drop('rerank_score', axis=1)
    result = ranked_books.head(k)
    return result


# def enhanced_apply_post_filters(books: pd.DataFrame, filters: dict, filterValidation: dict, k: int = 10) -> pd.DataFrame:
#     """
#     Enhanced post-filtering with advanced re-ranking.
#     Replaces the basic apply_post_filters function.
#     """
#     # First apply basic filtering (names/keywords)
#     if "names" in filters and filters["names"] is not None:
#         logger.info("APPLYING names filter")
#         names = filters["names"]
        
#         len_books_before = len(books)
#         name_mask = books["description"].str.contains('|'.join(names), case=False, na=False, regex=True)
#         books = books[name_mask]
        
#         validate_keywords_filter(books, filters["names"], filterValidation, len_books_before)
    
#     # Apply advanced re-ranking
#     reranked_books = rerank_books_by_keywords_and_tone(books, filters, k)
    
#     # Validate tone filtering if applied
#     if "tone" in filters and filters["tone"] is not None and filters["tone"] in tone_options:
#         validate_tone_filter(reranked_books, filters["tone"], filterValidation, len(books))
    
#     logger.info("Finished applying enhanced post filters with re-ranking")
#     return reranked_books

# perform the post filters tone and key_words
# prioritizing the names first, then just returning the top k sorted by tone
def apply_post_filters(books: pd.DataFrame, filters: dict, filterValidation: dict, k = 10) -> pd.DataFrame:

    # Filter books where any of the specified names appears in the description
    if "names" in filters and filters["names"] is not None:
        logger.info("APPLYING names filter")
        names = filters["names"]
        
        len_books_before = len(books)
        name_mask = books["description"].str.contains('|'.join(names), case=False, na=False, regex=True)
        books = books[name_mask]

        validate_keywords_filter(books, filters["names"], filterValidation, len_books_before)

    # Sort by tone and return the top k
    # added an extra check to be sure before sorting
    if "tone" in filters and filters["tone"] is not None and filters["tone"] in tone_options:
        len_books_before = len(books)
        books = books.sort_values(by=filters["tone"], ascending=False)
        
        validate_tone_filter(books, filters["tone"], filterValidation, len_books_before)

    logger.info("Finished applying post filters")
    return books.head(k)

if __name__ == "__main__":
    # quick smoke tests
    from config import BOOKS_PATH
    books = pd.read_parquet(BOOKS_PATH)

    # Example 1: Basic filtering
    filters = {
        "authors": ["George Orwell", "Aldous Huxley"],
        "genre": "Fiction",
        "pages_min": 100,
        "pages_max": 500
    }

    filtered_books = apply_pre_filters(books, filters, {})
    for book in filtered_books.itertuples():
        print(f"{book.title} by {book.authors} - {book.num_pages} pages")

    print("\n" + "="*60)
    print("TESTING RE-RANKING SYSTEM")
    print("="*60)

    # Example 2: Re-ranking with keywords and tone
    rerank_filters = {
        "keywords": ["love", "war", "future"],  # Keywords to search for
        "tone": "joy"  # Target emotional tone
    }

    # Get some books to re-rank (first 50 for testing)
    sample_books = books.head(50)
    
    print(f"\nRe-ranking {len(sample_books)} books with filters: {rerank_filters}")
    reranked = rerank_books_by_keywords_and_tone(sample_books, rerank_filters, k=10)
    
    print(f"\nTop 5 re-ranked books:")
    for i, book in enumerate(reranked.head(5).itertuples(), 1):
        score = getattr(book, 'rerank_score', 'N/A')
        tone_score = getattr(book, rerank_filters['tone'], 'N/A')
        print(f"{i}. {book.title}")
        print(f"   Rerank Score: {score:.3f}, {rerank_filters['tone']} tone: {tone_score:.3f}")
        print(f"   Author: {book.authors}")
        print()