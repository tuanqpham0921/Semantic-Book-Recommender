import json
from app.models import (
    BookRecommendationResponse, FilterValidationLog, 
    FilterSchema
)
from app.config import client, MODEL


def _so_overall(query: str, system: str, schema: dict, extra: dict | None = None) -> dict:
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


# -----------------------
# 1) explain the overal schema
# -----------------------
_EXPLAIN_OVERALL_SCHEMA = {
    "name": "ExplainOverall",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"tone": {"type": ["string", "null"]}},
        "required": ["tone"]
    }
}
_EXPLAIN_OVERALL_SYS = (
    "..."
)

def explain_overall_recommendation(request: BookRecommendationResponse) -> str:
    # Generate an explanation for the overall recommendation
    
    validation = request.validation
    content = request.content
    filters = request.filters

    out = _so_overall(content, _EXPLAIN_OVERALL_SYS, _EXPLAIN_OVERALL_SCHEMA)

    return "WORKING ON THE EXPLANATION"