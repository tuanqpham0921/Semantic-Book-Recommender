import pandas as pd

filter_categories = ["tone", "pages_max", "pages_min", "genre", "children", "names"]
genre_options = ("Fiction", "Non-Fiction", "Children's Fiction", "Children's Non-Fiction")

# Performs a semantic search using the ChromaDB 
# to retrieve book recommendations based on the input query.
def apply_filters(books: pd.DataFrame, filters: dict) -> pd.DataFrame:

    # get the Fiction/Non-Fiction genre first
    if "genre" in filters and filters["genre"] in ["Fiction", "Non-Fiction"]:
        genre = filters["genre"]
        if "children" in filters and filters["children"]:
            genre = "Children's " + genre
        books = books[books["simple_categories"] == genre]
        print(f"Has {len(books)} books after genre: {genre} filter.")

    if "pages_min" in filters:
        books = books[books["pages"] >= filters["pages_min"]]
    
    if "pages_max" in filters:
        books = books[books["pages"] <= filters["pages_max"]]

    # # *** This also go after the embedding search
    # if "names" in filters:
    #     books = books[books["names"].isin(filters["names"])]

    # # tone goes last as it is not a filter in the database
    # # *** TONE needs to be applied AFTER the vector embedding search!
    # if "tone" in filters:
    #     books.sort_values(by=filters["tone"], ascending=False, inplace=True)
    #     print(f"Has {len(books)} books after tone: {filters["tone"]} filter.")

    '''
        1. get filter
        2. validate filter (TODO)
        3. apply filter 
            * only (genre, pages_min/max, author)

        4. convert to Document then vector search

        5. Apply the tone sort filter first
        6. Apply the keywords filter next (take only top 10)
            * if there's not enough then takes others as well
    '''

    return books