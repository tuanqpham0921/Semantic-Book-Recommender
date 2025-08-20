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

# make sure that all the published years meet the criteria
def validate_published_year_filter(books: pd.DataFrame, published_year: dict, filterValidation: dict = None):
    filterValidation["applied_published_year"] = {}
    yearValidation = filterValidation["applied_published_year"]

    published_year_min = published_year.get("min", None)
    published_year_max = published_year.get("max", None)
    published_year_exact = published_year.get("exact", None)

    yearValidation["applied"] = True
    yearValidation["num_books_after"] = len(books)
    yearValidation["filter_value"] = published_year

    for index, book in books.iterrows():
        book_year = book.get("published_year", None)

        if not book_year: continue
        
        # Handle exact year match first (takes priority)
        if published_year_exact is not None:
            if book_year != published_year_exact:
                yearValidation["error"] = f"Failed Exact Published Year Filter, has {book_year}, expected {published_year_exact}"
                yearValidation["status"] = "failed"
                return
        else:
            # Handle min/max year range
            if published_year_min is not None and book_year <= published_year_min:
                yearValidation["error"] = f"Failed Min Published Year Filter, has {book_year}, expected >= {published_year_min}"
                yearValidation["status"] = "failed"
                return
            
            if published_year_max is not None and book_year >= published_year_max:
                yearValidation["error"] = f"Failed Max Published Year Filter, has {book_year}, expected < {published_year_max}"
                yearValidation["status"] = "failed"
                return
    
    # everything is good
    yearValidation["status"] = "success"



#------------------------------------------------------
#------------- POST FILTER VALIDATION -----------------
#------------------------------------------------------

# make sure that all the books have the keywords
def validate_keywords_filter(books: pd.DataFrame, keywords: list, filterValidation: dict):
    filterValidation["applied_keywords"] = {}
    keywordsValidation = filterValidation["applied_keywords"]

    keywordsValidation["applied"] = True
    keywordsValidation["num_books_after"] = len(books)
    keywordsValidation["filter_value"] = keywords

    for index, book in books.iterrows():
        if not pd.Series([book["description"]]).str.contains('|'.join(keywords), case=False, na=False, regex=True).any():
            keywordsValidation["error"]  = f"Failed Keywords Filter, has {book['description']}"
            keywordsValidation["status"] = "failed"
            return
    
    # everything is good
    keywordsValidation["status"] = "success"

# make sure that tone was applied
def validate_tone_filter(books: pd.DataFrame, tone: str, filterValidation: dict):
    filterValidation["applied_tone"] = {}
    toneValidation = filterValidation["applied_tone"]

    toneValidation["applied"] = True
    toneValidation["num_books_after"] = len(books)
    toneValidation["filter_value"] = tone
    
    # for tone we just need to know that it was applied
    toneValidation["status"] = "success"