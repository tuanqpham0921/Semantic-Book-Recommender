import logging
from fastapi import FastAPI
from typing import List
import pandas as pd

# Import models and configuration
from app.models import RecommendationRequest, BookRecommendation
from app.config import add_cors_middleware, db_books, BOOKS_PATH

# Import filter_query module from app folder
import app.filter_query as filter_query
import app.filter_df as filter_df

# Configure middleware
app = FastAPI()
add_cors_middleware(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# how many book we want to return
SIMILAR_K = 50
FINAL_K   = 10

def similarity_search_filtered(query: str, filtered_books: pd.DataFrame, db_books, k: int = 20):
    """
    Perform similarity search but only return results from the filtered DataFrame
    """
    if len(filtered_books) <= k:
        return filtered_books

    # Get all ISBNs from filtered books
    filtered_isbns = set(filtered_books['isbn13'].astype(str))
    
    # Do a larger ChromaDB search to ensure we have enough candidates
    search_k = min(k * 5, 400)  # Search more to account for filtering
    recs = db_books.similarity_search(query, k=search_k)
    
    # Extract ISBNs from ChromaDB results
    valid_results = []
    for rec in recs:
        isbn = rec.page_content.strip('"').split()[0]
        if isbn in filtered_isbns:
            valid_results.append(isbn)
        if len(valid_results) >= k:
            break
    
    # Return filtered books that match the similarity search
    return filtered_books[filtered_books['isbn13'].isin(valid_results)].head(k)


# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=List[BookRecommendation])
def recommend_books(request: RecommendationRequest):
    logger.info(f"REQUEST: {request}")

    # extract the filters here
    filters = filter_query.assemble_filters(request.description)
    logger.info(f"FILTERS: {filters}")

    # extract the main content here
    content = filter_query.extract_content(request.description, filters)
    logger.info(f"CONTENT: {content}")

    # load in a fresh patch of books
    books = pd.read_parquet(BOOKS_PATH)
    logger.info(f"BOOK LEN: {len(books)}")

    # apply pre-filters to the books
    books = filter_df.apply_pre_filters(books, filters)
    logger.info(f"PRE-FILTER BOOK LEN: {len(books)}")
        
    # Perform semantic search on the filtered books
    books = similarity_search_filtered(content, books, db_books, SIMILAR_K)
    logger.info(f"POST-SEARCH BOOK LEN: {len(books)}")

    # apply the post-filters
    books = filter_df.apply_post_filters(books, filters, FINAL_K)
    logger.info(f"POST-FILTER BOOK LEN: {len(books)}")

    # Convert DataFrame rows to BookRecommendation objects
    recommendations = [
        BookRecommendation(**row.to_dict())
        for _, row in books.iterrows()
    ]

    # Log the number of recommendations and their details
    logger.info(f"Returning {len(recommendations)} recommendations.")
    for rec in recommendations[:10]:
        logger.info(f"ISBN: {rec.isbn13}, Title: {rec.title}, Authors: {rec.authors}")

    return recommendations


# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
