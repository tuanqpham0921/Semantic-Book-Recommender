import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
BOOKS_PATH = os.getenv("BOOKS_PATH", "./data/books.csv")
COVER_NOT_FOUND_IMAGE = os.getenv("COVER_NOT_FOUND_IMAGE", "./data/cover-not-found.jpg")
TAGGED_DESCRIPTIONS_PATH = os.getenv("TAGGED_DESCRIPTIONS_PATH", "./data/tagged_descriptions.txt")