import pandas as pd
import logging

from app.filter_validation import (
    validate_author_filter, validate_genre_filter,
    validate_min_pages_filter, validate_max_pages_filter
)

# Get the logger (same configuration as main.py)
logger = logging.getLogger(__name__)

filter_categories = ("tone", "pages_max", "pages_min", "genre", "children", "names")
genre_options = ("Fiction", "Non-Fiction", "Children's Fiction", "Children's Non-Fiction")
tone_options = ("joy", "surprise", "anger", "fear", "sadness")

# perform the pre filters like Authors, Genre, and Pages
def apply_pre_filters(books: pd.DataFrame, filters: dict, filterValidation: dict) -> pd.DataFrame:
    # get the authors filters first
    if "author" in filters and filters["author"] is not None:
        logger.info("APPLYING authors filter")
        authors = filters["author"]

        # Filter books where any of the specified authors appears in the authors field
        author_mask = books["authors"].str.contains('|'.join(authors), case=False, na=False, regex=True)
        books = books[author_mask]
        
        # now we validate author filtering
        validate_author_filter(books, authors, filterValidation)
        

    # get the Fiction/Non-Fiction genre first
    if "genre" in filters and filters["genre"] in ["Fiction", "Non-Fiction"]:
        logger.info("APPLYING genre filter")
        genre = filters["genre"]
        if "children" in filters and filters["children"]:
            genre = "Children's " + genre
        books = books[books["simple_categories"] == genre]

        # now we validate genre filtering
        validate_genre_filter(books, genre, filterValidation)

    # min and max filter is last
    if "pages_min" in filters and filters["pages_min"] is not None:
        logger.info("APPLYING pages_min filter")
        books = books[books["num_pages"] >= filters["pages_min"]]
        logger.info(f"Has {len(books)} books after pages_min: {filters['pages_min']} filter.")

        validate_min_pages_filter(books, filters["pages_min"], filterValidation)

    if "pages_max" in filters and filters["pages_max"] is not None:
        logger.info("APPLYING pages_max filter")
        books = books[books["num_pages"] <= filters["pages_max"]]
        logger.info(f"Has {len(books)} books after pages_max: {filters['pages_max']} filter.")

        validate_max_pages_filter(books, filters["pages_max"], filterValidation)

    return books

# perform the post filters tone and key_words
# prioritizing the names first, then just returning the top k sorted by tone
def apply_post_filters(books: pd.DataFrame, filters: dict, k = 10) -> pd.DataFrame:

    # Filter books where any of the specified names appears in the description
    if "names" in filters and filters["names"] is not None:
        logger.info("APPLYING names filter")
        names = filters["names"]
        name_mask = books["description"].str.contains('|'.join(names), case=False, na=False, regex=True)
        books = books[name_mask]
        logger.info(f"Has {len(books)} books after names: {names} filter.")

    # Sort by tone and return the top k
    # added an extra check to be sure before sorting
    if "tone" in filters and filters["tone"] is not None and filters["tone"] in tone_options:
        logger.info("APPLYING tone filter")
        books = books.sort_values(by=filters["tone"], ascending=False)

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

    filtered_books = apply_pre_filters(books, filters)
    for book in filtered_books.itertuples():
        print(f"{book.title} by {book.authors} - {book.num_pages} pages")