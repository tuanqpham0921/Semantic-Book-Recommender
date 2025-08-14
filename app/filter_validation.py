import pandas as pd
import logging

# make sure that all authors are the requested author
def validate_author_filter(books: pd.DataFrame, authors: list, filterValidation: dict):
    filterValidation["applied_author"] = {}
    authorValidation = filterValidation["applied_author"]

    authorValidation["applied"] = True
    authorValidation["num_books_after"] = len(books)
    authorValidation["filter_value"] = authors
    
    joined_authors = '|'.join(authors)
    for index, book in books.iterrows():
        if not pd.Series([book["authors"]]).str.contains(joined_authors, case=False, na=False, regex=True).any():
            authorValidation["error"]  = f"Failed Author Filter, has {book['authors']}"
            authorValidation["status"] = "failed"
            return
    
    # everything is good
    authorValidation["status"] = "success"

# make sure that all genre are the requested genre
def validate_genre_filter(books: pd.DataFrame, genre: str, filterValidation: dict):
    filterValidation["applied_genre"] = {}
    genreValidation = filterValidation["applied_genre"]

    genreValidation["applied"] = True
    genreValidation["num_books_after"] = len(books)
    genreValidation["filter_value"] = genre

    for index, book in books.iterrows():
        if book["simple_categories"] != genre:
            genreValidation["error"]  = f"Failed Genre Filter, has {book['simple_categories']}"
            genreValidation["status"] = "failed"
            return
    
    # everything is good
    genreValidation["status"] = "success"

# make sure that all the pages are more than requested
def validate_min_pages_filter(books: pd.DataFrame, min_pages: int, filterValidation: dict):
    filterValidation["applied_min_pages"] = {}
    minPagesValidation = filterValidation["applied_min_pages"]

    minPagesValidation["applied"] = True
    minPagesValidation["num_books_after"] = len(books)
    minPagesValidation["filter_value"] = min_pages

    for index, book in books.iterrows():
        if book["num_pages"] < min_pages:
            minPagesValidation["error"]  = f"Failed Min Pages Filter, has {book['num_pages']}"
            minPagesValidation["status"] = "failed"
            return
    
    # everything is good
    minPagesValidation["status"] = "success"

# make sure that all the pages are less than requested
def validate_max_pages_filter(books: pd.DataFrame, max_pages: int, filterValidation: dict):
    filterValidation["applied_max_pages"] = {}
    maxPagesValidation = filterValidation["applied_max_pages"]

    maxPagesValidation["applied"] = True
    maxPagesValidation["num_books_after"] = len(books)
    maxPagesValidation["filter_value"] = max_pages

    for index, book in books.iterrows():
        if book["num_pages"] > max_pages:
            maxPagesValidation["error"]  = f"Failed Max Pages Filter, has {book['num_pages']}"
            maxPagesValidation["status"] = "failed"
            return
    
    # everything is good
    maxPagesValidation["status"] = "success"