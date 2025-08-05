import os
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd

# Assuming you have ChromaDB and your embedding function loaded here
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv
load_dotenv()

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
    allow_origins=["*"],
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

    print(f"Found {len(book_recs)} books matching the query.")

    # filter out the max number of pages if provided
    if max_pages is not None:
        book_recs = book_recs[book_recs["num_pages"] <= max_pages]

    print(f"Found {len(book_recs)} books matching the query after PAGE filter.")

    # if category is not "All", filter by category
    if category != "All":
        book_recs = book_recs[book_recs["simple_categories"] == category]

    print(f"Found {len(book_recs)} books matching the query after CATEGORY filter.")

    # only get the top recommendations based on the tone
    if tone != "All" and tone in tone_mapping:
        book_recs.sort_values(by=tone_mapping[tone], ascending=False, inplace=True)

    print(f"Found {len(book_recs)} books matching the query after TONE filter.")

    # get the top ten recommendations
    return book_recs.head(final_top_k)
    

# Endpoint to recommend books based on user query
@app.post("/recommend_books", response_model=List[BookRecommendation])
def recommend_books(request: RecommendationRequest):

    print("\n============================================")
    print("type(request): ", type(request))
    print(request)
    print("============================================\n")

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

    print("\n============================================")
    print(f"Returning {len(recommendations)} recommendations.")
    for rec in recommendations:
        print(f"ISBN: {rec.isbn13}, Title: {rec.title}, Authors: {rec.authors}")
    print("============================================\n")


    return recommendations

# place holder for API root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Recommendation API!"}
