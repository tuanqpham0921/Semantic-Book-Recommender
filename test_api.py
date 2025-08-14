import requests
import sys

recommend_books_url = "http://localhost:8000/recommend_books"
reason_query_url    = "http://localhost:8000/reason_query"

headers = {"Content-Type": "application/json"}
prompts = [
    "a book about forgiveness",
    "a 300 page or more books by Stephen King with a sad tone and take place in Maine",
    "get me books by Stephen King and J.K. Rowling"
]
#===================================================================

def print_result(result, query):
    print("=" * 110)
    print("QUERY: \n")
    print(query)

    # -------------------------------------------------
    print("=" * 110)
    # Print wider header row
    print(
        f"{'Title'[:60].ljust(62)}"
        f"{'Authors'[:30].ljust(32)}"
        f"{'Genre'[:25].ljust(27)}"
        f"{'Num Pages'.rjust(10)}"
    )
    print("-" * 110)

    for book in result:
        print(
            f"{book['title'][:60].ljust(62)}"
            f"{book['authors'][:30].ljust(32)}"
            f"{str(book['simple_categories'])[:25].ljust(27)}"
            f"{str(book['num_pages']).rjust(10)}"
        )
    print("=" * 110)

    # Print all unique authors (one-liner)
    authors_set = set([author.strip() for book in result for author in str(book['authors']).replace(';', ',').split(',') if author.strip()])
    print("Unique Authors: \n")
    print("\n".join(sorted(authors_set)))
    print("-" * 110)


    # Print all unique genres (one-liner)
    genres_set = set([genre.strip() for book in result for genre in str(book['simple_categories']).replace(';', ',').split(',') if genre.strip()])
    print("Unique Genres: \n")
    print("\n".join(sorted(genres_set)))
    print("-" * 110)

    # Print all unique num pages
    num_pages_set = set([book['num_pages'] for book in result if 'num_pages' in book])
    print("Unique Num Pages: \n")
    print(", ".join(sorted(map(str, num_pages_set))))

    print("=" * 110)


def print_validation(validation):

    for key, value in validation.items():
        if not value:
            print(f"No {key} validation to display.")
            print("-" * 110)
            continue

        print(f"{key.capitalize()}:")
        print("  applied:", value["applied"])
        print("  num_books_after:", value["num_books_after"])
        print("  filter_value:", value["filter_value"])
        print()
        print("  status:", value["status"])
        if value["status"] == "failed":
            print("  Error:", value["error"])

        print("-" * 110)


def filter_remove_none(filters):
    if not filters:
        return None

    result = {}
    for key, value in filters.items():
        if value is not None:
            result[key] = value

    return result

def get_reasoning(query, payload):
    response = requests.post(reason_query_url, json=payload, headers=headers)

    if not response.ok:
        print(f"Error {response.status_code}: {response.text}")
        quit()

    reasoning = response.json()
    # filters = filter_remove_none(reasoning["filters"])
    # reasoning["filters"] = filters

    return reasoning

def main():
    prompts = [
        "a book about forgiveness",
        "a 300 page or more books by Stephen King with a sad tone and take place in Maine",
        "get me books by Stephen King and J.K. Rowling"
    ]

    # If a query is passed as an argument, use it; otherwise use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = prompts[1]

    payload = {"description": query}
    reasoning = get_reasoning(query, payload)
    print(f"REASONING: \n{reasoning}")

    recommend_book_payload = {**payload, **reasoning}
    response = requests.post(recommend_books_url, json=recommend_book_payload, headers=headers)

    # there is nothing here so we just quit
    if not response.ok:
        print(f"Error {response.status_code}: {response.text}")
        quit()

    result = response.json()
    
    recomendations = result["recommendations"]
    print_result(recomendations, query)
    
    print("=" * 110)
    print("=" * 110)
    print()

    print_validation(result["validation"])
    print()


if __name__ == "__main__":
    main()