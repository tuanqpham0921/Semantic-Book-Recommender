import pandas as pd
import logging

# Generic validation function that handles the common structure
def _generic_validate_filter(books: pd.DataFrame, filter_value, filter_name: str, applied_key: str, filterValidation: dict, len_books_before: int, validation_func):
    """
    Generic validation function that handles common validation structure.
    
    Args:
        books: DataFrame of filtered books
        filter_value: The filter value to validate against
        filter_name: Name of the filter for messages (e.g., "authors", "genre")
        applied_key: Key for filterValidation dict (e.g., "applied_author")
        filterValidation: Dict to store validation results
        len_books_before: Number of books before filtering
        validation_func: Function that takes (book, filter_value) and returns (is_valid, error_message)
    """
    filterValidation[applied_key] = {}
    validation = filterValidation[applied_key]

    validation["applied"] = True
    validation["num_books_after"] = len(books)
    validation["num_books_before"] = len_books_before
    validation["filter_value"] = filter_value

    # Apply the specific validation logic
    for index, book in books.iterrows():
        is_valid, error_message = validation_func(book, filter_value)
        if not is_valid:
            validation["message"] = error_message
            validation["status"] = "failed"
            return
    
    # everything is good
    validation["status"] = "success"
    validation["message"] = f"Applied {filter_name}={filter_value}: narrowed {len_books_before} → {len(books)} books."

# Validation logic functions
def _validate_author_logic(book, authors):
    joined_authors = '|'.join(authors)
    is_valid = pd.Series([book["authors"]]).str.contains(joined_authors, case=False, na=False, regex=True).any()
    error_message = f"Failed Author Filter: Expected one of {authors}, but found '{book['authors']}'" if not is_valid else None
    return is_valid, error_message

def _validate_genre_logic(book, genre):
    is_valid = book["simple_categories"] == genre
    error_message = f"Failed Genre Filter: Expected '{genre}', but found '{book['simple_categories']}'" if not is_valid else None
    return is_valid, error_message

def _validate_min_pages_logic(book, min_pages):
    is_valid = book["num_pages"] >= min_pages
    error_message = f"Failed Min Pages Filter: Expected ≥{min_pages} pages, but found {book['num_pages']} pages" if not is_valid else None
    return is_valid, error_message

def _validate_max_pages_logic(book, max_pages):
    is_valid = book["num_pages"] <= max_pages
    error_message = f"Failed Max Pages Filter: Expected ≤{max_pages} pages, but found {book['num_pages']} pages" if not is_valid else None
    return is_valid, error_message

def _validate_keywords_logic(book, keywords):
    is_valid = pd.Series([book["description"]]).str.contains('|'.join(keywords), case=False, na=False, regex=True).any()
    error_message = f"Failed Keywords Filter: Expected keywords {keywords} in description, but description doesn't contain any of these terms" if not is_valid else None
    return is_valid, error_message

# make sure that all authors are the requested author
def validate_author_filter(books: pd.DataFrame, authors: list, filterValidation: dict, len_books_before: int):
    _generic_validate_filter(books, authors, "authors", "applied_author", filterValidation, len_books_before, _validate_author_logic)

# make sure that all genre are the requested genre
def validate_genre_filter(books: pd.DataFrame, genre: str, filterValidation: dict, len_books_before: int):
    _generic_validate_filter(books, genre, "genre", "applied_genre", filterValidation, len_books_before, _validate_genre_logic)

# make sure that all the pages are more than requested
def validate_min_pages_filter(books: pd.DataFrame, min_pages: int, filterValidation: dict, len_books_before: int):
    _generic_validate_filter(books, min_pages, "pages_min", "applied_min_pages", filterValidation, len_books_before, _validate_min_pages_logic)

# make sure that all the pages are less than requested
def validate_max_pages_filter(books: pd.DataFrame, max_pages: int, filterValidation: dict, len_books_before: int):
    _generic_validate_filter(books, max_pages, "pages_max", "applied_max_pages", filterValidation, len_books_before, _validate_max_pages_logic)

# make sure that all the published years meet the criteria
def validate_published_year_filter(books: pd.DataFrame, published_year: dict, filterValidation: dict, len_books_before: int):
    filterValidation["applied_published_year"] = {}
    yearValidation = filterValidation["applied_published_year"]

    yearValidation["applied"] = True
    yearValidation["num_books_after"] = len(books)
    yearValidation["num_books_before"] = len_books_before
    yearValidation["filter_value"] = published_year

    published_year_min = published_year.get("min", None)
    published_year_max = published_year.get("max", None)
    published_year_exact = published_year.get("exact", None)


    for index, book in books.iterrows():
        book_year = book.get("published_year", None)

        if not book_year: continue
        
        # Handle exact year match first (takes priority)
        if published_year_exact is not None:
            if book_year != published_year_exact:
                yearValidation["message"] = f"Failed Exact Published Year Filter: Expected year {published_year_exact}, but found {book_year}"
                yearValidation["status"] = "failed"
                return
        else:
            # Handle min/max year range
            if published_year_min is not None and book_year >= published_year_min:
                yearValidation["message"] = f"Failed Min Published Year Filter: Expected year >{published_year_min}, but found {book_year}"
                yearValidation["status"] = "failed"
                return
            
            if published_year_max is not None and book_year <= published_year_max:
                yearValidation["message"] = f"Failed Max Published Year Filter: Expected year <{published_year_max}, but found {book_year}"
                yearValidation["status"] = "failed"
                return
    
    # everything is good
    yearValidation["status"] = "success"
    
    # Build message based on which filters were applied
    filter_parts = []
    if published_year_exact is not None:
        filter_parts.append(f"exact={published_year_exact}")
    if published_year_min is not None:
        filter_parts.append(f"min={published_year_min}")
    if published_year_max is not None:
        filter_parts.append(f"max={published_year_max}")
    
    filter_description = ", ".join(filter_parts)
    yearValidation["message"] = f"Applied published_year ({filter_description}): narrowed {len_books_before} → {len(books)} books."



#------------------------------------------------------
#------------- POST FILTER VALIDATION -----------------
#------------------------------------------------------

# make sure that all the books have the keywords
def validate_keywords_filter(books: pd.DataFrame, keywords: list, filterValidation: dict, len_books_before: int):
    _generic_validate_filter(books, keywords, "keywords", "applied_keywords", filterValidation, len_books_before, _validate_keywords_logic)

# make sure that tone was applied
def validate_tone_filter(books: pd.DataFrame, tone: str, filterValidation: dict, len_books_before: int):
    filterValidation["applied_tone"] = {}
    toneValidation = filterValidation["applied_tone"]

    toneValidation["applied"] = True
    toneValidation["num_books_after"] = len(books)
    toneValidation["num_books_before"] = len_books_before
    toneValidation["filter_value"] = tone
    
    # for tone we just need to know that it was applied
    toneValidation["status"] = "success"
    toneValidation["message"] = f"Applied tone={tone}: sorted books by {tone} score, narrowed {len_books_before} → {len(books)} books."