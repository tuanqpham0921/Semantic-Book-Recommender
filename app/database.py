from sqlalchemy import Column, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class BookEmbedding(Base):
    __tablename__ = "book_embeddings"
    
    # Primary key
    isbn13 = Column(String, primary_key=True)
    
    # Basic book information
    isbn10 = Column(String)
    title = Column(String, nullable=False)
    authors = Column(String)
    categories = Column(String)
    simple_categories = Column(String)
    description = Column(Text)
    
    # Publication and rating info
    published_year = Column(Float)
    average_rating = Column(Float)
    num_pages = Column(Float)
    ratings_count = Column(Float)
    
    # Images
    thumbnail = Column(String)
    large_thumbnail = Column(String)
    
    # Additional metadata
    title_and_subtiles = Column(String)
    tagged_description = Column(Text)
    isbn = Column(String)
    
    # Emotion scores
    anger = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    neutral = Column(Float, default=0.0)
    
    # Vector embedding (1536 dimensions for OpenAI embeddings)
    embedding = Column(Vector(1536))
    
    def to_dict(self):
        """Convert to dictionary for BookRecommendation model"""
        return {
            'isbn13': self.isbn13,
            'isbn10': self.isbn10,
            'title': self.title,
            'authors': self.authors,
            'categories': self.categories,
            'simple_categories': self.simple_categories,
            'description': self.description,
            'published_year': int(self.published_year) if self.published_year else None,
            'average_rating': float(self.average_rating) if self.average_rating else 0.0,
            'num_pages': int(self.num_pages) if self.num_pages else None,
            'ratings_count': int(self.ratings_count) if self.ratings_count else None,
            'thumbnail': self.thumbnail,
            'large_thumbnail': self.large_thumbnail,
            'title_and_subtiles': self.title_and_subtiles,
            'tagged_description': self.tagged_description,
            'anger': float(self.anger) if self.anger else 0.0,
            'disgust': float(self.disgust) if self.disgust else 0.0,
            'fear': float(self.fear) if self.fear else 0.0,
            'joy': float(self.joy) if self.joy else 0.0,
            'sadness': float(self.sadness) if self.sadness else 0.0,
            'surprise': float(self.surprise) if self.surprise else 0.0,
            'neutral': float(self.neutral) if self.neutral else 0.0,
        }
