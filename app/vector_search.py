import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
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

def similarity_search_postgres(
    query: str, 
    books_df: pd.DataFrame, 
    db: Session, 
    k: int = 50
) -> pd.DataFrame:
    """
    Perform similarity search using PostgreSQL with pgvector
    """
    # Generate embedding for the query
    query_embedding = get_embedding(query)
    
    # Get ISBNs from the filtered books dataframe
    isbn_list = books_df['isbn13'].tolist()
    
    if not isbn_list:
        return pd.DataFrame()
    
    # Create placeholders for the IN clause
    isbn_placeholders = ','.join([f"'{isbn}'" for isbn in isbn_list])
    
    # Perform vector similarity search with cosine distance
    search_query = text(f"""
        SELECT 
            isbn13, isbn10, title, authors, categories, simple_categories,
            description, published_year, average_rating, num_pages, ratings_count,
            thumbnail, large_thumbnail, title_and_subtiles, tagged_description,
            anger, disgust, fear, joy, sadness, surprise, neutral,
            1 - (embedding <=> :query_embedding) AS similarity_score
        FROM book_embeddings
        WHERE isbn13 IN ({isbn_placeholders})
        ORDER BY embedding <=> :query_embedding
        LIMIT :k
    """)
    
    result = db.execute(
        search_query, 
        {
            "query_embedding": str(query_embedding), 
            "k": k
        }
    ).fetchall()
    
    # Convert results to DataFrame
    if not result:
        return pd.DataFrame()
    
    # Convert to list of dictionaries
    columns = [
        'isbn13', 'isbn10', 'title', 'authors', 'categories', 'simple_categories',
        'description', 'published_year', 'average_rating', 'num_pages', 'ratings_count',
        'thumbnail', 'large_thumbnail', 'title_and_subtiles', 'tagged_description',
        'anger', 'disgust', 'fear', 'joy', 'sadness', 'surprise', 'neutral', 'similarity_score'
    ]
    
    data = [dict(zip(columns, row)) for row in result]
    return pd.DataFrame(data)
