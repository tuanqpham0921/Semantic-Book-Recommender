import requests
import sys
import json

recommend_books_url = "http://localhost:8000/recommend_books"
reason_query_url    = "http://localhost:8000/reason_query"

headers = {"Content-Type": "application/json"}
prompts = [
    "a book about forgiveness",
    "a 300 page or more books by Stephen King with a sad tone and take place in Maine",
    "get me books by Stephen King and J.K. Rowling"
]

filters_names = ["genre", "author", "pages_min", "pages_max", "tone", "children", "names"]
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
        print("  num_books_before:", value["num_books_before"])
        print("  num_books_after:", value["num_books_after"])
        print("  filter_value:", value["filter_value"])
        print()
        print("  status:", value["status"])
        print("  message:", value["message"])

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
    print()
    print("-" * 110)
    print(f"REASONING QUERY: \n{query}\n")


    response = requests.post(reason_query_url, json=payload, headers=headers)

    if not response.ok:
        print(f"Error {response.status_code}: {response.text}")
        quit()

    reasoning = response.json()
    # filters = filter_remove_none(reasoning["filters"])
    # reasoning["filters"] = filters
    
    return reasoning

def process_query(query, payload, reasoning):

    print(f"PROCESSING QUERY: \n{query}")

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

    return 

def print_difference_reasoning(actual, expected):
    # if they are the same then skip
    
    # Remove null values from actual filters
    actual_cleaned = {}
    actual_cleaned["content"] = actual["content"]
    actual_cleaned["filters"] = None

    if actual.get("filters"):
        for k, v in actual["filters"].items():
            if not v: continue

            if k == "published_year":
                if v.get("min") is not None:
                    actual_cleaned["published_year_min"] = v["min"]
                if v.get("max") is not None:
                    actual_cleaned["published_year_max"] = v["max"]
                if v.get("exact") is not None:
                    actual_cleaned["published_year_exact"] = v["exact"]
            else:
                actual_cleaned[k] = v

    print("DIFFERENCE REASONING:")
    print("Actual:")
    print(json.dumps(actual_cleaned, indent=2))
    print("\nExpected:")
    print(json.dumps(expected, indent=2))

    print("\n")
    if actual_cleaned == expected:
        print("NO:  differences found.")
    else:
        print("YES:  differences found.")

def batch_test():
    # open the json file data_processing/etc/description_test_50.json
    with open("data_processing/etc/description_test_50.json", "r") as f:
        data = json.load(f)

    for item in data:
        payload = {"description": item["query"]}
        print(f"ID: {item['id']}\n")
        reasoning = get_reasoning(item["query"], payload)
        # result = process_query(item["query"], payload, reasoning)

        expected_reasoning = item["expected"]

        print_difference_reasoning(reasoning, expected_reasoning)

        print("-" * 110)

#================================================
#================================================
def single_test():
    query = "300 page or more books by Stephen King with a sad tone and take place in Maine"

    payload = {"description": query}
    
    reasoning = get_reasoning(query, payload)
    print(f"REASONING: \n{json.dumps(reasoning, indent=2)}\n")

    process_query(query, payload, reasoning)
#================================================
#================================================

def main():
    single_test()
    # batch_test()


if __name__ == "__main__":
    main()