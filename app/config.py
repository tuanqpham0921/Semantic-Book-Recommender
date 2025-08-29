import os
from fastapi.middleware.cors import CORSMiddleware
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
BOOKS_PATH = os.getenv("BOOKS_PATH", "./data/books.parquet")

# PostgreSQL Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:1234@localhost:5432/book_recommender"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load ChromaDB (keeping for backward compatibility during migration)
db_books = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
)

def add_cors_middleware(app):
    """Add CORS middleware to allow cross-origin requests"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://tuanqpham0921.com",
            "https://www.tuanqpham0921.com",
            "*"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )