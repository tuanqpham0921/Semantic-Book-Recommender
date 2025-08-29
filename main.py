#!/usr/bin/env python3
"""
Entry point for the Book Recommendation FastAPI application.
This file imports the FastAPI app from the app module.
"""

from app.main import app

# Export the app for external use (uvicorn, tests, etc.)
__all__ = ["app"]

# This allows the app to be run directly with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
