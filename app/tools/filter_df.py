import pandas as pd
import logging

# Get the logger (same configuration as main.py)
logger = logging.getLogger(__name__)

filter_categories = ("tone", "pages_max", "pages_min", "genre", "children", "names")
genre_options = ("Fiction", "Nonfiction", "Children's Fiction", "Children's Nonfiction")
tone_options = ("joy", "surprise", "anger", "fear", "sadness")


# perform the post filters tone and key_words
# prioritizing the names first, then just returning the top k sorted by tone
def rerank_books_by_keywords_and_tone(books: pd.DataFrame, filters: dict, k = 10) -> pd.DataFrame:
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
        keywords_list = filters.get("keywords")
        logger.info(f"Re-ranking based on keywords: {keywords_list}")
        
        for keyword in keywords_list:
            # Score based on keyword frequency in description (case-insensitive)
            # Convert to lowercase for case-insensitive counting
            keyword_freq = ranked_books['description'].str.lower().str.count(keyword.lower()).fillna(0)
            
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

if __name__ == "__main__":
    # quick smoke tests
    from ..config import BOOKS_PATH
    books = pd.read_parquet(BOOKS_PATH)

    filters = {
        "authors": ["George Orwell", "Aldous Huxley"],
        "genre": "Fiction",
        "pages_min": 100,
        "pages_max": 500
    }

    # NOTE: apply_pre_filters has been moved to PostgreSQL level
    # This is just a placeholder for testing post_filters
    print("Pre-filters have been moved to PostgreSQL vector search")
    print("Testing post_filters only...")
    
    filterValidation = {}
    filtered_books = apply_post_filters(books.head(10), {"tone": "joy"}, filterValidation)
    for book in filtered_books.itertuples():
        print(f"{book.title} by {book.authors}")