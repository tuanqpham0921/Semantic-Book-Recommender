
import json
from typing import Dict, Any, List

from app.config import client, MODEL
from better_profanity import profanity

profanity.load_censor_words()

def _so(query: str, system: str, schema: dict, extra: dict | None = None) -> dict:
    """Single-call Structured Output helper (Chat Completions API)."""
    user_payload = {"query": query}
    if extra:  # pass filters or flags to the model
        user_payload["context"] = extra
        
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_schema", "json_schema": schema},
        temperature=0,
        seed=7,
    )
    return json.loads(resp.choices[0].message.content)


_VALIDATION_SCHEMA = {
    "name": "QueryValidation",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_valid": {"type": "boolean"}
        },
        "required": ["is_valid"]
    }
}

# Simple validation system prompt
_VALIDATION_SYS = (
    "You are a content validator for a book recommendation system.\n\n"
    
    "Analyze the user's query and return is_valid: true if it could reasonably be a book search request.\n\n"
    
    "ACCEPT queries that:\n"
    "1. Are written in English (or mostly English)\n"
    "2. Contain book-related terms like genres (horror, romance, sci-fi, mystery, etc.)\n"
    "3. Include descriptive words commonly used for books (scary, funny, sad, exciting, dark, romantic, etc.)\n"
    "4. Mention authors, titles, topics, or book characteristics\n"
    "5. Have filters like page count, publication year, etc.\n"
    "6. Make basic sense as a book search request\n"
    "7. Are single words that could describe books (e.g., 'scary', 'romantic', 'thriller')\n\n"
    
    "REJECT queries that are:\n"
    "- Completely non-English text\n"
    "- Random gibberish or keyboard mashing (e.g., 'asdfghjkl', 'qwerty uiop')\n"
    "- Just numbers or punctuation with no book context\n"
    "- Spam, URLs, or promotional content unrelated to books\n"
    "- Code snippets or technical jargon unrelated to books\n"
    "- Profanity or offensive content\n\n"
    
    "Be permissive for book-related content - single descriptive words like 'scary', 'funny', 'romantic' are valid book searches."
)

def is_valid_query(query: str) -> bool:
    """Check if a query is valid (English, no profanity, makes sense).
    
    Args: query: The user's query to validate
    Returns: True if valid, False if invalid
    """
    if not query or not query.strip():
        return False
    
    # Quick profanity check first
    if profanity.contains_profanity(query):
        return False
    
    # less strict check
    try:
        result = _so(query.strip(), _VALIDATION_SYS, _VALIDATION_SCHEMA)
        return result.get("is_valid", False)
    except Exception as e:
        print(f"Error validating query: {e}")
        return False
    

def remove_keywords_duplicates(keywords: List[str], filters: Dict[str, Any]):
    """Remove duplicate keywords from the filters in-place.

    Matching is performed case-insensitively (normalized with strip().lower()).
    The function mutates the provided `keywords` list so callers that rely on
    in-place behavior continue to work.
    """

    if not keywords: return

    def _norm(s: str) -> str:
        return s.strip().lower()

    # Build a set of normalized tokens to remove based on filter instances
    tokens_to_remove = set()
    if filters:
        for key, value in filters.items():
            if not value:
                continue

            if isinstance(value, str):
                tokens_to_remove.add(_norm(value))
            elif isinstance(value, (int, float)):
                tokens_to_remove.add(_norm(str(value)))
            elif key == "published_year" and isinstance(value, dict):
                for year_key in ("min", "max", "exact"):
                    y = value.get(year_key)
                    if y is not None:
                        tokens_to_remove.add(_norm(str(y)))

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        tokens_to_remove.add(_norm(item))

    # Filter names in-place while preserving original order and removing duplicates
    cleaned = []
    seen = set()
    for n in keywords:
        # Preserve non-string items as-is (avoid accidental dropping)
        kn = _norm(n)
        if kn in tokens_to_remove or kn in seen:
            continue

        cleaned.append(n)
        seen.add(kn)

    keywords.clear()
    keywords.extend(cleaned)


if __name__ == "__main__":
    # quick smoke tests
    q1 = "adfasfwfwfasda "
    q1_res = json.dumps(is_valid_query(q1), indent=2, ensure_ascii=False)
    print(q1_res)
    print("------------------------------------------------")