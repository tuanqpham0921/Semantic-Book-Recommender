from pydantic import BaseModel, Field
from typing import Union, List, Optional

# Define Query Body
class QueryRequest(BaseModel):
    description: str

# The Filter Schema
class FilterSchema(BaseModel):
    genre: Optional[str] = Field(default=None)
    author: Optional[List[str]] = Field(default=None)
    pages_min: Optional[int] = Field(default=None)
    pages_max: Optional[int] = Field(default=None)
    tone: Optional[str] = Field(default=None)
    children: Optional[bool] = Field(default=None)
    names: Optional[List[str]] = Field(default=None)
    # published_year: Optional[int] = Field(default=None)

class ReasoningResponse(BaseModel):
    filters: FilterSchema
    content: str

class RecommendBooksRequest(BaseModel):
    description: str
    filters: FilterSchema
    content: str

# Define Response with all requested fields
class BookRecommendation(BaseModel):
    isbn13: str = Field(default="")
    title: str = Field(default="")
    authors: Union[str, None] = Field(default="")
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

# log the filtering
class ValidationLog(BaseModel):
    applied: bool
    num_books_after: int
    filter_value: Optional[Union[str, List[str], int]] = None
    status: str # "success", "failed", "skipped"
    error: Optional[str] = None  # Only populated if status == "failed"

class FilterValidationLog(BaseModel):
    applied_author: Optional[ValidationLog] = None
    applied_genre:  Optional[ValidationLog] = None
    applied_min_pages: Optional[ValidationLog] = None
    applied_max_pages: Optional[ValidationLog] = None
    applied_keywords:  Optional[ValidationLog] = None
    applied_tone:     Optional[ValidationLog] = None

class BookRecommendationResponse(BaseModel):
    recommendations: List[BookRecommendation]
    validation: FilterValidationLog
    filters: FilterSchema
    content: str