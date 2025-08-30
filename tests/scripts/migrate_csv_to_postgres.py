#!/usr/bin/env python3
"""
Migration script to load book data from CSV into PostgreSQL with vector embeddings
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import Base, BookEmbedding
from app.tools.vector_search import get_embedding
from app.config import DATABASE_URL

load_dotenv()

def clean_numeric_value(value):
    """Clean and convert numeric values, handling NaN and None"""
    if pd.isna(value) or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def migrate_books_from_csv():
    """Load books from CSV file and migrate to PostgreSQL with embeddings"""
    
    print("Starting migration from CSV to PostgreSQL...")
    
    # Create database tables
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Load CSV data
    csv_path = "data_processing/etc/books.csv"
    print(f"Loading books from {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    books_df = pd.read_csv(csv_path)
    print(f"Loaded {len(books_df)} books from CSV")
    
    # Print column names to understand the structure
    print("Available columns:", books_df.columns.tolist())
    
    db = SessionLocal()
    
    try:
        batch_size = 50  # Smaller batch size for embedding generation
        total_books = len(books_df)
        migrated_count = 0
        
        for i in tqdm(range(0, total_books, batch_size), desc="Migrating books"):
            batch = books_df.iloc[i:i+batch_size]
            
            for _, book in batch.iterrows():
                # Check if book already exists
                existing_book = db.query(BookEmbedding).filter(
                    BookEmbedding.isbn13 == str(book['isbn13'])
                ).first()
                
                if existing_book:
                    print(f"Skipping existing book: {book['isbn13']}")
                    continue
                
                # Generate embedding for the book
                text_to_embed = f"{book.get('title', '')} {book.get('description', '')}"
                if pd.isna(text_to_embed) or text_to_embed.strip() == '':
                    text_to_embed = book.get('title', 'Unknown Book')
                
                try:
                    embedding = get_embedding(text_to_embed)
                except Exception as e:
                    print(f"Failed to generate embedding for {book['isbn13']}: {e}")
                    continue
                
                # Create BookEmbedding record
                book_embedding = BookEmbedding(
                    isbn13=str(book['isbn13']),
                    isbn10=str(book.get('isbn10', '')) if pd.notna(book.get('isbn10')) else '',
                    title=str(book.get('title', '')),
                    authors=str(book.get('authors', '')),
                    categories=str(book.get('categories', '')),
                    simple_categories=str(book.get('simple_categories', '')),
                    description=str(book.get('description', '')),
                    published_year=clean_numeric_value(book.get('published_year')),
                    average_rating=clean_numeric_value(book.get('average_rating')),
                    num_pages=clean_numeric_value(book.get('num_pages')),
                    ratings_count=clean_numeric_value(book.get('ratings_count')),
                    thumbnail=str(book.get('thumbnail', '')),
                    large_thumbnail=str(book.get('large_thumbnail', '')),
                    title_and_subtiles=str(book.get('title_and_subtiles', '')),
                    tagged_description=str(book.get('tagged_description', '')),
                    isbn=str(book.get('isbn', '')),
                    anger=clean_numeric_value(book.get('anger')) or 0.0,
                    disgust=clean_numeric_value(book.get('disgust')) or 0.0,
                    fear=clean_numeric_value(book.get('fear')) or 0.0,
                    joy=clean_numeric_value(book.get('joy')) or 0.0,
                    sadness=clean_numeric_value(book.get('sadness')) or 0.0,
                    surprise=clean_numeric_value(book.get('surprise')) or 0.0,
                    neutral=clean_numeric_value(book.get('neutral')) or 0.0,
                    embedding=embedding
                )
                
                db.add(book_embedding)
                migrated_count += 1
            
            # Commit batch
            try:
                db.commit()
                print(f"Committed batch {i//batch_size + 1}/{(total_books + batch_size - 1)//batch_size}")
            except Exception as e:
                db.rollback()
                print(f"Error committing batch: {e}")
                continue
        
        print(f"Migration completed! Migrated {migrated_count} books.")
        
        # Print summary
        total_migrated = db.query(BookEmbedding).count()
        print(f"Total books in database: {total_migrated}")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    migrate_books_from_csv()
