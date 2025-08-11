import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
BOOKS_PATH = os.getenv("BOOKS_PATH", "./data/books.parquet")

TONE_MAP = {
    "joy": {"joy", "happy", "happiness", "uplifting", "cheerful", "positive", "hopeful"},
    "sadness": {"sadness", "sad", "melancholy", "depressing", "tragic"},
    "anger": {"anger", "angry", "rage", "furious", "mad"},
    "fear": {"fear", "scary", "terrifying", "horror", "anxious"},
    "disgust": {"disgust", "gross", "revolting", "nauseating"},
    "surprise": {"surprise", "shocking", "unexpected", "astonishing"},
    "neutral": {"neutral", "objective", "calm", "matter-of-fact"}
}

# Load the CSV file into a pandas DataFrame
# books = pd.read_parquet(BOOKS_PATH)
with open("prompt_text.txt", "r", encoding="utf-8") as f:
    SYSTEM = f.read()

with open("search_schema.json", "r", encoding="utf-8") as f:
    SEARCH_SCHEMA = json.load(f)

with open("description_test_50.json", "r", encoding="utf-8") as f:
    TEST_50 = json.load(f)

#####################################################################################################
#####################################################################################################
#####################################################################################################

client = OpenAI()

def extract_query_filters(user_description: str) -> dict:
    """Returns dict matching SEARCH_SCHEMA (content + filters)."""
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",  # supports json_schema response_format
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({"description": user_description}, ensure_ascii=False)}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": SEARCH_SCHEMA
        },
        temperature=0,
        seed=7,  # optional: more reproducible outputs
    )
    # With Structured Outputs + strict, the text is guaranteed to match the schema
    return json.loads(response.choices[0].message.content)

# Example
if __name__ == "__main__":
    
    simple = "a book about love that's less than 500 pages but more than 123 pages"
    print(extract_query_filters(simple))
    print("--------------------------------------------------------------------")

    for cur_test in TEST_50:
        query = cur_test["query"]
        print(query)

        result = extract_query_filters(query)
        print(result)
        print()
