import requests
import sys
import json
import textwrap
import argparse
import os
from datetime import datetime

url = "http://localhost:8000/"
recommend_books_url = f"{url}recommend_books"
reason_query_url    = f"{url}reason_query"
explain_overall_recommendation_url = f"{url}explain_overall_recommendation"

headers = {"Content-Type": "application/json"}
prompts = [
    "a book about forgiveness",
    "a 300 page or more books by Stephen King with a sad tone and take place in Maine",
    "get me books by Stephen King and J.K. Rowling"
]

filters_names = ["genre", "author", "pages_min", "pages_max", "tone", "children", "keywords"]
#===================================================================

def print_result(result, query):
    print("=" * 119)
    print("QUERY: \n")
    print(query)

    # -------------------------------------------------
    print("=" * 119)
    # Print wider header row
    print(
        f"{'Title'[:60].ljust(65)}"
        f"{'Rank Score'.ljust(15)}"
        f"{'Authors'[:30].ljust(32)}"
        f"{'Genre'[:25].ljust(27)}"
        f"{'Num Pages'.rjust(10)}"
    )
    print("-" * 119)

    for i, book in enumerate(result, 1):
        # Safely get values with fallbacks
        title = book.get('title', 'Unknown Title')
        authors = book.get('authors', 'Unknown Author')
        categories = book.get('simple_categories', 'Unknown Genre')
        num_pages = book.get('num_pages', 'N/A')
        rerank_score = book.get('rerank_score', 0.0)
    
        
        print(
            f"{str(title)[:60].ljust(65)}"
            f"{f'{rerank_score:.2f}'.ljust(15)}"
            f"{str(authors)[:30].ljust(32)}"
            f"{str(categories)[:25].ljust(27)}"
            f"{str(num_pages).rjust(10)}"
        )
    print("=" * 119)

    # Print all unique authors (one-liner)
    authors_set = set()
    for book in result:
        authors = book.get('authors', '')
        if authors and authors != 'None':
            author_list = str(authors).replace(';', ',').split(',')
            for author in author_list:
                if author.strip():
                    authors_set.add(author.strip())
    
    print("Unique Authors: \n")
    if authors_set:
        print("\n".join(sorted(authors_set)))
    else:
        print("None")
    print("-" * 110)


    # Print all unique genres (one-liner)
    genres_set = set()
    for book in result:
        categories = book.get('simple_categories', '')
        if categories and categories != 'None':
            genre_list = str(categories).replace(';', ',').split(',')
            for genre in genre_list:
                if genre.strip():
                    genres_set.add(genre.strip())
    
    print("Unique Genres: \n")
    if genres_set:
        print("\n".join(sorted(genres_set)))
    else:
        print("None")
    print("-" * 110)

    # Print all unique num pages
    num_pages_set = set()
    for book in result:
        pages = book.get('num_pages')
        if pages is not None and pages != 'None':
            num_pages_set.add(pages)
    
    print("Unique Num Pages: \n")
    if num_pages_set:
        print(", ".join(sorted(map(str, num_pages_set))))
    else:
        print("None")

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

    return result

def print_difference_reasoning(actual, expected):
    # if they are the same then skip
    
    # Remove null values from actual filters
    actual_cleaned = {}
    actual_cleaned["content"] = actual["content"]
    actual_cleaned["filters"] = {}

    if actual.get("filters"):
        for k, v in actual["filters"].items():
            if not v or not k: continue

            if k == "published_year":
                if v.get("min") is not None:
                    actual_cleaned["filters"]["published_year_min"] = v["min"]
                if v.get("max") is not None:
                    actual_cleaned["filters"]["published_year_max"] = v["max"]
                if v.get("exact") is not None:
                    actual_cleaned["filters"]["published_year_exact"] = v["exact"]
            else:
                actual_cleaned["filters"][k] = v

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

# --------------------------------------------

def print_explanation(result):
    print("=" * 110)
    print("EXPLANATION:")
    print("=" * 110)
    
    if "explain_overall_recommendation" not in result:
        print("No explanation found.")
        print("=" * 110)
        return

    explanation_text = result["explain_overall_recommendation"]
    
    # Use textwrap to format the explanation nicely
    wrapped_text = textwrap.fill(
        explanation_text, 
        width=100,  # Maximum line width
        initial_indent="  ",  # Indent first line
        subsequent_indent="  ",  # Indent continuation lines
        break_long_words=False,  # Don't break words
        break_on_hyphens=False   # Don't break on hyphens
    )
    
    print(wrapped_text)
    print("=" * 110)
    print()

def get_overall_explanation(recommendation_response):

    overal_validaiton_payload = recommendation_response
    response = requests.post(explain_overall_recommendation_url, json=overal_validaiton_payload, headers=headers)

    result = response.json()

    return result


def batch_test():
    # Create logs directory if it doesn't exist
    os.makedirs("batch_test_logs", exist_ok=True)
    
    # Generate timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"batch_test_logs/batch_test_{timestamp}.txt"
    
    # Redirect stdout to log file
    original_stdout = sys.stdout
    with open(log_file, 'w') as f:
        sys.stdout = f
        
        # open the json file data_processing/etc/description_test_50.json
        with open("data_processing/etc/description_test_50.json", "r") as data_file:
            data = json.load(data_file)

        for item in data:
            payload = {"description": item["query"]}
            print(f"ID: {item['id']}")
            reasoning = get_reasoning(item["query"], payload)

            expected_reasoning = item["expected"]
            print_difference_reasoning(reasoning, expected_reasoning)

            recomendation_response = process_query(item["query"], payload, reasoning)
            
            overall_explanation = get_overall_explanation(recomendation_response)

            print("=" * 110)
            print(f"PROCESSING QUERY: \n{item['query']}")
            print_explanation(overall_explanation)

            print("-" * 110)
    
    # Restore stdout
    sys.stdout = original_stdout
    print(f"Batch test completed. Results saved to: {log_file}")

#================================================
#================================================
def single_test():
    query = "I want something like The Midnight Library but less depressing"

    payload = {"description": query}
    
    reasoning = get_reasoning(query, payload)
    print(f"REASONING: \n{json.dumps(reasoning, indent=2)}\n")

    recomendation_response = process_query(query, payload, reasoning)

    overall_explanation = get_overall_explanation(recomendation_response)
    print_explanation(overall_explanation)



#================================================
#================================================

def main():
    parser = argparse.ArgumentParser(description='Run API tests')
    parser.add_argument('--mode', choices=['single', 'batch'], default='single',
                       help='Test mode: single or batch (default: single)')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        single_test()
    elif args.mode == 'batch':
        batch_test()


if __name__ == "__main__":
    main()