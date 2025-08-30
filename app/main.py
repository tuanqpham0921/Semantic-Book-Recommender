import logging
from fastapi import FastAPI, Depends
import pandas as pd
from sqlalchemy.orm import Session

# Import models and configuration
from app.models import QueryRequest, BookRecommendation, ReasoningResponse, RecommendBooksRequest, BookRecommendationResponse
from app.config import add_cors_middleware, get_db

# Import filter_query module from tools folder
from app.tools import filter_query
from app.tools import filter_df
from app.tools.vector_search import similarity_search_postgres

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


# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=BookRecommendationResponse)
def recommend_books(request: RecommendBooksRequest, db: Session = Depends(get_db)):
    filters = filter_query.assemble_filters(request.description)
    content = filter_query.extract_content(request.description, filters)

    if not content or not content.strip():
        content = request.description

    # Perform semantic search with filters directly in PostgreSQL
    books_df = similarity_search_postgres(content, filters, db, SIMILAR_K)


    # apply the post-filters (if needed for any additional processing)
    books_df = filter_df.rerank_books_by_keywords_and_tone(books_df, filters, FINAL_K)

    

# place holder for API root endpoint
@app.head('/health')
@app.get('/health')
def health_check():
    return 'ok'