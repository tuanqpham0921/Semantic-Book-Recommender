import logging
from fastapi import FastAPI
from typing import List
import pandas as pd

# Import models and configuration
from app.models import RecommendationRequest, BookRecommendation
from app.config import add_cors_middleware, db_books, BOOKS_PATH, filter_categories

# Import filter_query module from app folder
import app.filter_query as filter_query

# Configure middleware
app = FastAPI()
add_cors_middleware(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=List[BookRecommendation])
def recommend_books(request: RecommendationRequest):
    logger.info(f"request: {request}")

    # extract the filters here
    filters = filter_query.assemble_filters(request.description)
    logger.info(f"filters: {filters}")

    # extract the main content here
    content = filter_query.extract_content(request.description, filters)
    logger.info(f"content: {content}")

    print("================================")
    print(f"Filters: {filters}")
    print("================================")
    print(f"Content: {content}")
    print("================================")

    books = pd.read_parquet(BOOKS_PATH)
    if filters:
        books = filter_query.apply_filters(books, filters)
        print("================================")
        print(f"Filtered Books: {books}")
        print("================================")

    return []

# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
