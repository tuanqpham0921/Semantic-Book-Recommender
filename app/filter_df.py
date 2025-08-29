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

filter_categories = ("tone", "pages_max", "pages_min", "genre", "children", "names")
genre_options = ("Fiction", "Nonfiction", "Children's Fiction", "Children's Nonfiction")
tone_options = ("joy", "surprise", "anger", "fear", "sadness")


# perform the post filters tone and key_words
# prioritizing the names first, then just returning the top k sorted by tone
def apply_post_filters(books: pd.DataFrame, filters: dict, filterValidation: dict, k = 10) -> pd.DataFrame:

    # Filter books where any of the specified names appears in the description
    if "names" in filters and filters["names"] is not None:
        logger.info("APPLYING names filter")
        names = filters["names"]
        name_mask = books["description"].str.contains('|'.join(names), case=False, na=False, regex=True)
        books = books[name_mask]

        validate_keywords_filter(books, filters["names"], filterValidation)

    # Sort by tone and return the top k
    # added an extra check to be sure before sorting
    if "tone" in filters and filters["tone"] is not None and filters["tone"] in tone_options:
        books = books.sort_values(by=filters["tone"], ascending=False)
        
        validate_tone_filter(books, filters["tone"], filterValidation)

    logger.info("Finished applying post filters")
    return books.head(k)

if __name__ == "__main__":
    # quick smoke tests
    from config import BOOKS_PATH
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