import json
import os
import pandas as pd
import re
from typing import Optional, Dict, Any, List

from app.config import client, MODEL

filter_categories = ["tone", "pages_max", "pages_min", "genre", "children", "names"]
# Add published_year_exact to filter categories
filter_categories += ["published_year_min", "published_year_max", "published_year_exact"]

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

# -----------------------
# 1) Tone (exact phrase)
# -----------------------
_TONE_SCHEMA = {
    "name": "ToneExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"tone": {"type": ["string", "null"]}},
        "required": ["tone"]
    }
}
_TONE_SYS = (
    "Return JSON for the schema. Extract the exact tone/mood phrase if present "
    "(e.g., 'somber', 'dark humor', 'not sad', 'warm and comforting'). "
    "Do NOT infer or rephrase. If no tone words, set tone to null."
)
def extract_tone(query: str) -> Optional[str]:
    out = _so(query, _TONE_SYS, _TONE_SCHEMA)
    return out["tone"]

# -----------------------
# 2) Pages (min/max)
# -----------------------
_PAGES_SCHEMA = {
    "name": "PagesExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "pages_min": {"type": ["integer", "null"], "minimum": 0},
            "pages_max": {"type": ["integer", "null"], "minimum": 0},
        },
        "required": ["pages_min", "pages_max"]
    }
}
_PAGES_SYS = (
    "Return JSON for the schema. Extract numeric page bounds if explicitly stated:\n"
    "- pages_min for phrases like 'at least N', 'N or more', 'over N', 'more than N'.\n"
    "- pages_max for phrases like 'under N', 'less than N', 'no more than N', 'max N'.\n"
    "If not stated, set the respective value to null. Do not infer."
)
def extract_pages(query: str) -> Dict[str, Optional[int]]:
    out = _so(query, _PAGES_SYS, _PAGES_SCHEMA)
    return {"pages_min": out["pages_min"], "pages_max": out["pages_max"]}

# -----------------------
# Published Year (min/max)
# -----------------------
# Published Year (min/max/exact)
_YEAR_SCHEMA = {
    "name": "PublishedYearExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "published_year_min": {"type": ["integer", "null"], "minimum": 0},
            "published_year_max": {"type": ["integer", "null"], "minimum": 0},
            "published_year_exact": {"type": ["integer", "null"], "minimum": 0},
        },
        "required": ["published_year_min", "published_year_max", "published_year_exact"]
    }
}
_YEAR_SYS = (
    "Return JSON for the schema. Extract numeric published year bounds if explicitly stated:\n"
    "- published_year_min for phrases like 'published after N', 'written after N', 'from N', 'N or later', 'since N'.\n"
    "- published_year_max for phrases like 'published before N', 'written before N', 'up to N', 'until N', 'no later than N'.\n"
    "- published_year_exact for phrases like 'published in N', 'written in N', 'N edition', 'N year', 'exactly N'.\n"
)
def extract_published_year(query: str) -> Dict[str, Optional[int]]:
    out = _so(query, _YEAR_SYS, _YEAR_SCHEMA)
    return {
        "min": out["published_year_min"],
        "max": out["published_year_max"],
        "exact": out["published_year_exact"]
    }

# -----------------------
# 3) Genre (literal only)
# -----------------------
_GENRE_SCHEMA = {
    "name": "GenreExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"genre": {"type": ["string", "null"], "enum": ["fiction", "non-fiction", None]}},
        "required": ["genre"]
    }
}
_GENRE_SYS = (
    "Return JSON for the schema. Set genre ONLY if the query literally contains "
    "the word 'fiction' OR a non-fiction variant ('non-fiction', 'nonfiction', 'non fiction', any case). "
    "Normalize any non-fiction variant to 'non-fiction'. If not present, genre=null. Do not infer from 'sci-fi' etc."
    "Out put can only be 'Fiction' or 'Nonfiction' case sensitive"
)

NONFICTION_RE = re.compile(r'(?<![A-Za-z])non[^A-Za-z]*fiction', re.I)
FICTION_RE    = re.compile(r'(?<![A-Za-z])fiction', re.I)

def standardized_genre(genre_text: str) -> Optional[str]:
    genre_text = genre_text.strip().lower()
    if not genre_text: return None

    if NONFICTION_RE.search(genre_text): return "Nonfiction"
    if FICTION_RE.search(genre_text):    return "Fiction"
    return genre_text

def extract_genre(query: str) -> Optional[str]:
    out = _so(query, _GENRE_SYS, _GENRE_SCHEMA)

    # None or it's an empty string
    if not out["genre"]: return None
    
    return standardized_genre(out["genre"])

# -----------------------
# 4) Children flag
# -----------------------
_CHILDREN_SCHEMA = {
    "name": "ChildrenExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"children": {"type": "boolean"}},
        "required": ["children"]
    }
}
_CHILDREN_SYS = (
    "Return JSON for the schema. Set children=true if the query mentions children/kid/kids/child/children’s/"
    "childrens/kids' (any case). Otherwise children=false. Do not infer."
)
def extract_children(query: str) -> bool:
    out = _so(query, _CHILDREN_SYS, _CHILDREN_SCHEMA)
    return out["children"]

# -----------------------
# 5) Names (exact phrases)
# -----------------------
_NAMES_SCHEMA = {
    "name": "NamesExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "names": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["names"]
    }
}
_NAMES_SYS = (
    "Return JSON for the schema. Extract exact proper names/terms from the query (places, regions, countries, "
    "cities, planets, nationalities, historical events, decades tokens), e.g., 'New York', 'Asia', 'UK', 'Mars', "
    "'World War II', '1980s', preserving the original casing as written. Do NOT include generic nouns "
    "like 'dragons', 'terraforming', 'first contact'. Do NOT include author names. If none, return an empty list."
)
def extract_names(query: str) -> List[str]:
    out = _so(query, _NAMES_SYS, _NAMES_SCHEMA)
    return out["names"]


# -----------------------
# 6) CONTENT: extract the core content using the composed filters
# -----------------------
_CONTENT_SCHEMA = {
    "name": "ContentExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"content": {"type": "string"}},
        "required": ["content"]
    }
}

def extract_content(query: str, filters: Dict[str, Any] | None, drop_names: bool = False) -> str:
    """
    Build the core 'content' string by removing filter-like statements:
      - tone phrases (if provided)
      - page constraints (at least/under/etc.)
      - genre tokens (fiction / non-fiction)
      - children/kid/kids/child markers
      - optionally names (if drop_names=True)
    Keep the rest of the semantic request intact. Do NOT invent new info.
    """
    # System prompt keeps it tight + deterministic
    _CONTENT_SYS = (
        "Return JSON for the schema. Rewrite the user's query into a short, natural phrase "
        "that captures only the core search topic. Remove any filter/constraint language:\n"
        "- tone words/phrases (e.g., 'somber', 'not sad', 'dark humor')\n"
        "- page limits (at least/under/no more than/N pages, etc.)\n"
        "- explicit genre tokens: 'fiction', 'non-fiction', 'nonfiction', 'non fiction'\n"
        "- children markers: children/children’s/child/childrens/kid/kids/kids'\n"
        f"- names/locations ONLY IF context.drop_names is true.\n"
        "Keep topic-defining words (e.g., 'about first contact'). Do not add or infer details. "
        "Return only the 'content' field."
    )

    context = {
        "filters": filters or {},
        "drop_names": bool(drop_names)
    }
    out = _so(query, _CONTENT_SYS, _CONTENT_SCHEMA, extra=context)
    return out["content"]

# -----------------------
# 5) Author (exact phrases)
# -----------------------
_AUTHORS_SCHEMA = {
    "name": "AuthorsExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "names": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["names"]
    }
}
_AUTHORS_SYS = (
    "Return JSON for the schema. Extract exact proper author names from the query (including full names, initials, "
    "and pen names), e.g., 'J.K. Rowling', 'Ernest Hemingway', 'Isaac Asimov', preserving the original casing as written. "
    "Do NOT include generic nouns like 'writers', 'poets', or 'novelists'. If none, return an empty list."
)
def extract_authors(query: str) -> List[str]:
    out = _so(query, _AUTHORS_SYS, _AUTHORS_SCHEMA)
    return out["names"]

# ------------------------------
# ----- Compose everything -----
# ------------------------------

def assemble_filters(query: str) -> Dict[str, Any]:
    tone = extract_tone(query)
    pages = extract_pages(query)
    genre = extract_genre(query)
    child = extract_children(query)
    names = extract_names(query)
    author = extract_authors(query)

    years = extract_published_year(query)

    filters: Dict[str, Any] = {}
    if tone: filters["tone"] = tone
    if pages.get("pages_min") is not None: filters["pages_min"] = pages["pages_min"]
    if pages.get("pages_max") is not None: filters["pages_max"] = pages["pages_max"]
    if genre: filters["genre"] = genre
    if child: filters["children"] = True
    if names: filters["names"] = names
    if author: filters["author"] = author

    # Only add published_year if at least one value is not None
    if any(value is not None for value in years.values()):
        filters["published_year"] = years

    return filters

def extract_query_filters(query: str, drop_names_from_content: bool = False) -> dict:
    """
    Full pipeline:
      1) assemble filters (sparse dict)
      2) extract content using query + filters
      3) return {content, filters|None}
    """
    filters = assemble_filters(query)
    content = extract_content(query, filters, drop_names=drop_names_from_content)
    return {"query": query, "content": content, "filters": (filters if filters else None)}

if __name__ == "__main__":
    # quick smoke tests
    q1 = "a book written before 2019"
    q1_res = json.dumps(extract_published_year(q1), indent=2, ensure_ascii=False)
    print(q1_res)
    print("------------------------------------------------")

    # # load in the 50 tests
    # with open("data_processing/etc/description_test_50.json", "r") as f:
    #     tests = json.load(f)

    # # run and print the results
    # with open("result_50.txt", "w") as f:
    #     for i, test in enumerate(tests):
    #         query = test["query"]
    #         res = extract_query_filters(query)
    #         print(f"Test {i + 1}:")
    #         print(json.dumps(res, indent=2, ensure_ascii=False))
    #         f.write(json.dumps(res, indent=2, ensure_ascii=False))
    #         print("------------------------------------------------")
            