import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd

# Assuming you have ChromaDB and your embedding function loaded here
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# from dotenv import load_dotenv
# load_dotenv()

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
BOOKS_PATH = os.getenv("BOOKS_PATH", "./data/books.parquet")

# Load ChromaDB
db_books = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
)
books = pd.read_parquet(BOOKS_PATH)

app = FastAPI()

# Define Request Body
class RecommendationRequest(BaseModel):
    description: str
    filters: Optional[dict] = None  # Optional filters like pages, genre, etc.

# Define Response with all requested fields
class BookRecommendation(BaseModel):
    isbn13: str = Field(default="")
    title: str = Field(default="")
    authors: str = Field(default="")
    categories: str = Field(default="")
    thumbnail: str = Field(default="")
    description: str = Field(default="")
    published_year: Optional[int] = Field(default=None)
    average_rating: float = Field(default=0.0)
    num_pages: Optional[int] = Field(default=None) # allow for nullable integers
    ratings_count: Optional[int] = Field(default=None)
    title_and_subtiles: str = Field(default="")
    tagged_description: str = Field(default="")
    simple_categories: str = Field(default="")
    anger: float = Field(default=0.0)
    disgust: float = Field(default=0.0)
    fear: float = Field(default=0.0)
    joy: float = Field(default=0.0)
    sadness: float = Field(default=0.0)
    surprise: float = Field(default=0.0)
    neutral: float = Field(default=0.0)

    class Config:
        extra = 'allow'  # Allow extra fields if necessary

# Performs a semantic search using the ChromaDB to retrieve book recommendations
# based on the input query.
def retrieve_semantic_recommendations(
        query: str,
        initial_top_k: int = 10,
) -> pd.DataFrame:
    recs = db_books.similarity_search(query, k=initial_top_k)
    books_list = [rec.page_content.strip('"').split()[0] for rec in recs]
    book_recs = books[books["isbn13"].isin(books_list)].head(initial_top_k)
    return book_recs

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=List[BookRecommendation])
def recommend_books(request: RecommendationRequest):
    # Embed user query
    df = retrieve_semantic_recommendations(request.description)
    
    # Convert DataFrame rows to BookRecommendation objects
    recommendations = [
        BookRecommendation(**row.to_dict())
        for _, row in df.iterrows()
    ]
    return recommendations

# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
