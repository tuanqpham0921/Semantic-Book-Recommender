
import json
import sys
import os
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
    
    "Analyze the user's query and return is_valid: true ONLY if ALL of these are met:\n"
    "1. Written in English (or mostly English)\n"
    "2. Contains no profanity, offensive language, or inappropriate content\n"
    "3. Makes basic sense as a book search request\n"
    "4. Not spam, gibberish, or meaningless text\n\n"
    
    "Return is_valid: false for:\n"
    "- Non-English text\n"
    "- Any profanity or offensive content\n"
    "- Nonsensical gibberish\n"
    "- Spam or inappropriate requests\n\n"
    
    "Be strict - when in doubt, return false."
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
    
    # OpenAI moderation check
    try:
        moderation = client.moderations.create(
            model="omni-moderation-latest",
            input=query.strip()
        )
        if moderation.results[0].flagged:
            return False
    except Exception as e:
        print(f"Error in moderation check: {e}")
        # Continue to AI validation if moderation fails
    
    try:
        result = _so(query.strip(), _VALIDATION_SYS, _VALIDATION_SCHEMA)
        return result.get("is_valid", False)
    except Exception as e:
        print(f"Error validating query: {e}")
        return False

if __name__ == "__main__":
    # quick smoke tests
    q1 = "adfasfwfwfasda "
    q1_res = json.dumps(is_valid_query(q1), indent=2, ensure_ascii=False)
    print(q1_res)
    print("------------------------------------------------")