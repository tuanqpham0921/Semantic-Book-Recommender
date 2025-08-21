import logging
from fastapi import FastAPI
from typing import List
import pandas as pd

# Import models and configuration
from app.models import (
    QueryRequest, BookRecommendation, 
    ReasoningResponse, RecommendBooksRequest, 
    BookRecommendationResponse, OverallExplanationResponse
)
from app.config import add_cors_middleware, db_books, BOOKS_PATH

# Import filter_query module from app folder
import app.filter_query as filter_query
import app.filter_df as filter_df
from app.search import similarity_search_filtered
import app.generate_reason as generate_reason
from app.query_validation import is_valid_query

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
    if not is_valid_query(request.description):
        return ReasoningResponse(
            content="Invalid query, Please try again",
            filters={},
            is_valid=False
        )

    filters = filter_query.assemble_filters(request.description)
    # logger.info(f"FILTERS:\n {filters}")
    # logger_separator()

    content = filter_query.extract_content(request.description, filters)
    # logger.info(f"CONTENT:\n {content}")
    # logger_separator()
    
    return ReasoningResponse(
            content=content, 
            filters=filters,
            is_valid=True
        )


@app.post("/explain_overall_recommendation", response_model=OverallExplanationResponse)
def explain_overall_recommendation(request: BookRecommendationResponse):
    messages = generate_reason.get_response_messages(request)

    # priortize no books found first
    if len(request.recommendations) == 0:
        explanation = generate_reason.explain_no_books_found(messages)
    
    # there are books 
    elif len(messages) == 0:
        explanation = generate_reason.explain_no_filter_applied(request.content)
    else:
        explanation = generate_reason.explain_overall_recommendation(messages)

    return {"explain_overall_recommendation": explanation}

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=BookRecommendationResponse)
def recommend_books(request: RecommendBooksRequest):
    # logger_separator()
    # logger.info(f"\nREQUEST: {request}")
    # logger_separator()

    filters = request.filters.dict()
    # logger.info(f"FILTERS:\n {filters}")
    # logger_separator()

    content = request.content
    # logger.info(f"CONTENT:\n {content}")
    # logger_separator()

    # load in a fresh patch of books
    books = pd.read_parquet(BOOKS_PATH)
    # logger.info(f"BOOK LEN: {len(books)}")
    # logger_separator()

    # make a filtervalidation
    filterValidation = {}
    # apply pre-filters to the books
    books = filter_df.apply_pre_filters(books, filters, filterValidation)
    # logger.info(f"\nPRE-FILTER BOOK LEN: {len(books)}")
    # logger_separator()

    # Perform semantic search on the filtered books
    books = similarity_search_filtered(content, books, db_books, SIMILAR_K)
    # logger.info(f"\nPOST-SEARCH BOOK LEN: {len(books)}")
    # logger_separator()

    # apply the post-filters
    books = filter_df.apply_post_filters(books, filters, filterValidation, FINAL_K)
    # logger.info(f"\nPOST-FILTER BOOK LEN: {len(books)}")
    # logger_separator()

    # # Log the number of recommendations and their details
    # logger.info(f"Returning {len(books)} recommendations:\n")
    # for _, row in books.head(DEBUG_K).iterrows():
    #     logger.info(f"ISBN: {row['isbn13']}, Title: {row['title']}, Authors: {row['authors']}")
    
    # logger_separator()

    # compose the response for recommend_books
    return BookRecommendationResponse(
        recommendations = [
            BookRecommendation(**row.to_dict())
            for _, row in books.iterrows()
        ],
        validation = filterValidation,
        filters = filters,
        content = content
    )


# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
