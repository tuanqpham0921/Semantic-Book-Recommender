import pandas as pd
import logging

logger = logging.getLogger(__name__)

def similarity_search_filtered(query: str, filtered_books: pd.DataFrame, db_books, k: int = 20):
    """
    Perform similarity search but only return results from the filtered DataFrame
    
    Args:
        query: The search query string
        filtered_books: DataFrame of books already filtered by pre-filters
        db_books: ChromaDB collection for similarity search
        k: Maximum number of results to return
        
    Returns:
        DataFrame of books matching both filters and similarity search, limited to k results
    """
    if len(filtered_books) <= k:
        return filtered_books

    # Get all ISBNs from filtered books
    filtered_isbns = set(filtered_books['isbn13'].astype(str))
    
    # Do a larger ChromaDB search to ensure we have enough candidates
    search_k = min(k * 5, 400)  # Search more to account for filtering
    recs = db_books.similarity_search(query, k=search_k)
    
    # Extract ISBNs from ChromaDB results
    valid_results = []
    for rec in recs:
        # Parse ISBN from format: "<isbn> <description>"
        parts = rec.page_content.strip().split()
        if parts:
            isbn = parts[0]
            if isbn in filtered_isbns:
                valid_results.append(isbn)
            if len(valid_results) >= k:
                break
    
    # Return filtered books that match the similarity search
    return filtered_books[filtered_books['isbn13'].isin(valid_results)].head(k)
