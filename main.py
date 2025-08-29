import logging
from fastapi import FastAPI, Depends
from typing import List
import pandas as pd
from sqlalchemy.orm import Session

# Import models and configuration
from app.models import QueryRequest, BookRecommendation, ReasoningResponse, RecommendBooksRequest, BookRecommendationResponse
from app.config import add_cors_middleware, get_db
from app.database import BookEmbedding

# Import filter_query module from app folder
import app.filter_query as filter_query
import app.filter_df as filter_df
from app.vector_search import similarity_search_postgres

# Configure middleware
app = FastAPI()
add_cors_middleware(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Suppress HTTP request logs from OpenAI and other libraries
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# how many book we want to return
SIMILAR_K = 50
FINAL_K   = 10
DEBUG_K   = 5

def logger_separator():
    logger.info("\n" + "="*50 + "\n")

@app.post("/reason_query", response_model=ReasoningResponse)
def reason_query_endpoint(request: QueryRequest):
    filters = filter_query.assemble_filters(request.description)
    # logger.info(f"FILTERS:\n {filters}")
    # logger_separator()

    content = filter_query.extract_content(request.description, filters)
    # logger.info(f"CONTENT:\n {content}")
    # logger_separator()

    return {"content": content, "filters": filters}

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=BookRecommendationResponse)
def recommend_books(request: RecommendBooksRequest, db: Session = Depends(get_db)):
    # logger_separator()
    # logger.info(f"\nREQUEST: {request}")
    # logger_separator()

    filters = request.filters.dict()
    # logger.info(f"FILTERS:\n {filters}")
    # logger_separator()

    content = request.content
    # logger.info(f"CONTENT:\n {content}")
    # logger_separator()

    # make a filtervalidation
    filterValidation = {}

    # Perform semantic search with filters directly in PostgreSQL
    books_df = similarity_search_postgres(content, filters, db, SIMILAR_K)
    # logger.info(f"\nPOST-SEARCH BOOK LEN: {len(books_df)}")
    # logger_separator()

    # apply the post-filters (if needed for any additional processing)
    books_df = filter_df.apply_post_filters(books_df, filters, filterValidation, FINAL_K)
    # logger.info(f"\nPOST-FILTER BOOK LEN: {len(books_df)}")
    # logger_separator()

    # Log the number of recommendations and their details
    logger.info(f"Returning {len(books_df)} recommendations:\n")
    for _, row in books_df.head(DEBUG_K).iterrows():
        logger.info(f"ISBN: {row['isbn13']}, Title: {row['title']}, Authors: {row['authors']}")
    
    # logger_separator()

    # compose the response for recommend_books
    return BookRecommendationResponse(
        recommendations = [
            BookRecommendation(**row.to_dict())
            for _, row in books_df.iterrows()
        ],
        validation = filterValidation,
        filters = filters,
        content = content
    )


# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
