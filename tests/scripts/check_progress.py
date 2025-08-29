#!/usr/bin/env python3
"""
Quick utility to check migration progress
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.database import BookEmbedding

def check_progress():
    """Check how many books have been migrated"""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        count = db.query(BookEmbedding).count()
        print(f"Books migrated so far: {count}")
        
        if count > 0:
            # Show a sample book
            sample = db.query(BookEmbedding).first()
            print(f"Sample book: {sample.title} by {sample.authors}")
        
        db.close()
        
    except Exception as e:
        print(f"Error checking progress: {e}")

if __name__ == "__main__":
    check_progress()
