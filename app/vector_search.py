import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.database import BookEmbedding

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model="text-embedding-3-small") -> List[float]:
    """Generate embedding for given text"""
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def build_author_filter(author_value: str, params: Dict[str, Any]) -> str:
    """Build SQL condition for author filtering"""
    params["authors"] = f"%{author_value.lower()}%"
    return "LOWER(authors) LIKE :authors"

def build_category_filter(category_value: str, params: Dict[str, Any]) -> str:
    """Build SQL condition for category filtering"""
    params["categories"] = f"%{category_value.lower()}%"
    return "LOWER(categories) LIKE :categories OR LOWER(simple_categories) LIKE :categories"

def build_year_filter(year_value: Any, params: Dict[str, Any]) -> str:
    """Build SQL condition for published year filtering"""
    conditions = []
    if isinstance(year_value, dict):
        if year_value.get("min"):
            params["min_year"] = year_value["min"]
            conditions.append("published_year >= :min_year")
        if year_value.get("max"):
            params["max_year"] = year_value["max"]
            conditions.append("published_year <= :max_year")
    else:
        params["year"] = year_value
        conditions.append("published_year = :year")
    return " AND ".join(conditions)

def build_rating_filter(rating_value: Any, params: Dict[str, Any]) -> str:
    """Build SQL condition for average rating filtering"""
    conditions = []
    if isinstance(rating_value, dict):
        if rating_value.get("min"):
            params["min_rating"] = rating_value["min"]
            conditions.append("average_rating >= :min_rating")
        if rating_value.get("max"):
            params["max_rating"] = rating_value["max"]
            conditions.append("average_rating <= :max_rating")
    else:
        params["rating"] = rating_value
        conditions.append("average_rating >= :rating")
    return " AND ".join(conditions)

def build_pages_filter(pages_value: Any, params: Dict[str, Any]) -> str:
    """Build SQL condition for page count filtering"""
    conditions = []
    if isinstance(pages_value, dict):
        if pages_value.get("min"):
            params["min_pages"] = pages_value["min"]
            conditions.append("num_pages >= :min_pages")
        if pages_value.get("max"):
            params["max_pages"] = pages_value["max"]
            conditions.append("num_pages <= :max_pages")
    else:
        params["pages"] = pages_value
        conditions.append("num_pages <= :pages")
    return " AND ".join(conditions)

def build_where_clause_and_params(filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Build WHERE clause and parameters for SQL query based on filters
    
    Args:
        filters: Dictionary of filter criteria
        
    Returns:
        Tuple of (where_clause_string, parameters_dict)
    """
    where_conditions = []
    params = {}
    
    # Filter mapping - maps filter keys to their corresponding builder functions
    filter_builders = {
        "authors": build_author_filter,
        "categories": build_category_filter,
        "published_year": build_year_filter,
        "average_rating": build_rating_filter,
        "num_pages": build_pages_filter
    }
    
    # Build conditions for each filter
    for filter_key, filter_value in filters.items():
        if filter_value and filter_key in filter_builders:
            condition = filter_builders[filter_key](filter_value, params)
            if condition:
                where_conditions.append(condition)
    
    # Construct WHERE clause
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    return where_clause, params

def build_similarity_search_query(where_clause: str) -> str:
    """Build the complete similarity search SQL query"""
    return f"""
        SELECT 
            isbn13, isbn10, title, authors, categories, simple_categories,
            description, published_year, average_rating, num_pages, ratings_count,
            thumbnail, large_thumbnail, title_and_subtiles, tagged_description,
            anger, disgust, fear, joy, sadness, surprise, neutral,
            1 - (embedding <=> :query_embedding) AS similarity_score
        FROM book_embeddings
        {where_clause}
        ORDER BY embedding <=> :query_embedding
        LIMIT :k
    """

def execute_search_query(db: Session, query: str, params: Dict[str, Any]) -> List:
    """Execute the search query and return results"""
    search_query = text(query)
    return db.execute(search_query, params).fetchall()

def convert_results_to_dataframe(results: List) -> pd.DataFrame:
    """Convert SQL query results to pandas DataFrame"""
    if not results:
        return pd.DataFrame()
    
    columns = [
        'isbn13', 'isbn10', 'title', 'authors', 'categories', 'simple_categories',
        'description', 'published_year', 'average_rating', 'num_pages', 'ratings_count',
        'thumbnail', 'large_thumbnail', 'title_and_subtiles', 'tagged_description',
        'anger', 'disgust', 'fear', 'joy', 'sadness', 'surprise', 'neutral', 'similarity_score'
    ]
    
    data = [dict(zip(columns, row)) for row in results]
    return pd.DataFrame(data)

def similarity_search_postgres(
    query: str, 
    filters: dict, 
    db: Session, 
    k: int = 50
) -> pd.DataFrame:
    """
    Perform similarity search using PostgreSQL with pgvector and apply filters
    
    Args:
        query: Search query text for embedding generation
        filters: Dictionary of filter criteria (authors, categories, etc.)
        db: SQLAlchemy database session
        k: Maximum number of results to return
        
    Returns:
        DataFrame containing search results with similarity scores
    """
    # Step 1: Generate embedding for the query
    query_embedding = get_embedding(query)
    
    # Step 2: Build WHERE clause and parameters from filters
    where_clause, filter_params = build_where_clause_and_params(filters)
    
    # Step 3: Add embedding and limit parameters
    params = {
        "query_embedding": str(query_embedding),
        "k": k,
        **filter_params
    }
    
    # Step 4: Build and execute the search query
    search_query = build_similarity_search_query(where_clause)
    results = execute_search_query(db, search_query, params)
    
    # Step 5: Convert results to DataFrame and return
    return convert_results_to_dataframe(results)
