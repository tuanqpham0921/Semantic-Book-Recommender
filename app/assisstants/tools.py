from pydantic import BaseModel, Field
from typing import Optional
from app.db import search_vector_db
from app.openai import get_embedding

# TQP: search through the knowledge base
# uses K nears neighbors
class QueryKnowledgeBaseTool(BaseModel):
    """Query the knowledge base to answer user questions about new technology trends, their applications and broader impacts."""
    query_input: str = Field(description='The natural language query input string. The query input should be clear and standalone.')

    async def __call__(self, rdb):
        query_vector = await get_embedding(self.query_input)
        chunks = await search_vector_db(rdb, query_vector)
        formatted_sources = [f"SOURCE: {c['doc_name']}\n\"\"\"\n{c['text']}\n\"\"\"" for c in chunks]
        return f"\n\n---\n\n".join(formatted_sources) + f"\n\n---"


class ExtractFilterAndGetContent(BaseModel):
    """Parse user queries and extract relevant filters for book searches from the database."""
    query_input: str = Field(description='The user query to parse and extract book search filters from.')
    
    async def __call__(self, rdb):
        # TODO: Implement filter extraction logic
        # This should parse the query and extract filters like genre, author, publication year, etc.
        pass


class FindBookSimilaritySearch(BaseModel):
    """Find books similar to the user's interests or queries using semantic search."""
    search_query: str = Field(description='The search query to find similar books in the database.')
    
    async def __call__(self, rdb):
        # TODO: Implement book similarity search logic
        # This should use vector similarity to find books matching the query
        pass


class QuestionAboutProject(BaseModel):
    """Answer questions about the book recommendation system itself."""
    question: str = Field(description='Question about how the book recommendation system works.')
    
    async def __call__(self, rdb):
        # TODO: Implement system information responses
        # This should provide information about the book database, capabilities, etc.
        pass


class FindSpecificBook(BaseModel):
    """Find a specific book by title, author, or ISBN."""
    title: Optional[str] = Field(description='The book title to search for', default=None)
    author: Optional[str] = Field(description='The author name to search for', default=None)
    isbn: Optional[str] = Field(description='The ISBN to search for', default=None)
    
    async def __call__(self, rdb):
        # TODO: Implement specific book search logic
        # This should search for exact matches by title, author, or ISBN
        pass


class GetBookDetails(BaseModel):
    """Get detailed information about a specific book."""
    book_id: str = Field(description='The unique identifier of the book to get details for')
    
    async def __call__(self, rdb):
        # TODO: Implement book details retrieval
        # This should fetch comprehensive book metadata, summary, reviews, etc.
        pass


class FilterBooks(BaseModel):
    """Filter books by specific criteria like genre, publication year, page count, etc."""
    genre: Optional[str] = Field(description='Filter by genre (e.g., "fantasy", "mystery", "romance")', default=None)
    author: Optional[str] = Field(description='Filter by author name', default=None)
    min_year: Optional[int] = Field(description='Minimum publication year', default=None)
    max_year: Optional[int] = Field(description='Maximum publication year', default=None)
    min_pages: Optional[int] = Field(description='Minimum page count', default=None)
    max_pages: Optional[int] = Field(description='Maximum page count', default=None)
    rating_min: Optional[float] = Field(description='Minimum rating (0-5)', default=None)
    language: Optional[str] = Field(description='Book language (e.g., "English", "Spanish")', default=None)
    
    async def __call__(self, rdb):
        # TODO: Implement book filtering logic
        # This should filter books based on the provided criteria
        pass


class GetSimilarBooks(BaseModel):
    """Find books similar to a specific book."""
    book_title: str = Field(description='The title of the book to find similar books for')
    book_author: Optional[str] = Field(description='The author of the reference book (helps with disambiguation)', default=None)
    limit: Optional[int] = Field(description='Number of similar books to return', default=10)
    
    async def __call__(self, rdb):
        # TODO: Implement similar books search logic
        # This should find books similar to the specified book based on content, genre, themes, etc.
        pass
