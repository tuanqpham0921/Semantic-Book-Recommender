import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

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

from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tuanqpham0921.com",
        "https://www.tuanqpham0921.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Request Body
class RecommendationRequest(BaseModel):
    description: str
    filters: Optional[dict] = None  # Optional filters like pages, genre, etc.

# Define Response with all requested fields
class BookRecommendation(BaseModel):
    isbn13: str = Field(default="")
    title: str = Field(default="")
    authors: str = Field(default="")
    categories: Optional[str] = Field(default=None)
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

# filter mapping for tones
# This maps the tone names to the corresponding column names in the DataFrame.
tone_mapping = {
    "Happy": "joy",
    "Surprising": "surprise",
    "Angry": "anger",
    "Suspenseful": "fear",
    "Sad": "sadness"
}

# Performs a semantic search using the ChromaDB 
# to retrieve book recommendations based on the input query.
def retrieve_semantic_recommendations(
        query: str,
        category: str = "All",
        tone: str = "All",
        max_pages: Optional[int] = None,
        initial_top_k: int = 50,
        final_top_k: int = 10
) -> pd.DataFrame:
    recs = db_books.similarity_search(query, k=initial_top_k)
    books_list = [rec.page_content.strip('"').split()[0] for rec in recs]
    book_recs = books[books["isbn13"].isin(books_list)].head(initial_top_k)
    logger.info(f"Found {len(book_recs)} books matching the query.")

    # filter out the max number of pages if provided
    if max_pages is not None:
        book_recs = book_recs[book_recs["num_pages"] <= max_pages]
        logger.info(f"Has {len(book_recs)} books after max_pages: {max_pages} filter.")

    # if category is not "All", filter by category
    if category != "All":
        book_recs = book_recs[book_recs["simple_categories"] == category]
        logger.info(f"Has {len(book_recs)} books after category: {category} filter.")


    # only get the top recommendations based on the tone
    if tone != "All" and tone in tone_mapping:
        book_recs.sort_values(by=tone_mapping[tone], ascending=False, inplace=True)
        logger.info(f"Has {len(book_recs)} books after tone: {tone} filter.")

    # log the number of books after all filters
    if len(book_recs) == 0:
        logger.warning("No books found matching the query after all filters.")
        return pd.DataFrame()
    elif len(book_recs) < final_top_k:
        logger.warning(f"Less than the requested number of {final_top_k} recommendations available.")
        return book_recs

    # get the top ten recommendations
    return book_recs.head(final_top_k)
    

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=List[BookRecommendation])
def recommend_books(request: RecommendationRequest):
    logger.info(f"request: {request}")

    # Embed user query
    df = retrieve_semantic_recommendations(request.description,
                                           request.filters["category"],
                                           request.filters["tone"],
                                           request.filters.get("max_pages", None))

    # Convert DataFrame rows to BookRecommendation objects
    recommendations = [
        BookRecommendation(**row.to_dict())
        for _, row in df.iterrows()
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
