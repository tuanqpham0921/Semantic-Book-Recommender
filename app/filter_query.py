import json
import re
from typing import Optional, Dict, Any, List

from app.config import client, MODEL
from app.query_validation import remove_keywords_duplicates

filter_categories = ["tone", "pages_max", "pages_min", "genre", "children", "keywords"]
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
tone_options = ("anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral")

_TONE_SCHEMA = {
    "name": "ToneExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"tone": {"type": ["string", "null"], "enum": list(tone_options) + [None]}},
        "required": ["tone"]
    }
}
_TONE_SYS = (
    "Return JSON for the schema. Map tone/mood phrases to one of the specific enum values: "
    "anger, disgust, fear, joy, sadness, surprise, neutral. "
    "Examples of mapping with HIGH CONFIDENCE:\n"
    "- 'happy', 'uplifting', 'cheerful', 'optimistic', 'not sad' → 'joy'\n"
    "- 'scary', 'frightening', 'terrifying', 'horror' → 'fear'\n"
    "- 'depressing', 'melancholy', 'tragic', 'heartbreaking' → 'sadness'\n"
    "- 'furious', 'enraged', 'hostile', 'bitter' → 'anger'\n"
    "- 'shocking', 'unexpected', 'twist', 'plot twist' → 'surprise'\n"
    "- 'revolting', 'repulsive', 'sickening', 'nauseating' → 'disgust'\n"
    "- 'balanced', 'objective', 'even-toned', 'matter-of-fact', 'neither happy nor sad' → 'neutral'\n"
    "Only return a value if you can map with HIGH CONFIDENCE. "
    "If ambiguous, vague, or no clear tone detected, return null."
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
            "pages_max": {"type": ["integer", "null"], "minimum": 0}
        },
        "required": ["pages_min", "pages_max"]
    }
}
_PAGES_SYS = (
    "Return JSON for the schema. Extract numeric page constraints ONLY if the query explicitly mentions 'page' or 'pages' with a number:\n"
    "- pages_min for phrases like 'at least N pages', 'N or more pages', 'over N pages', 'more than N pages' (INCLUSIVE - use the exact number N)\n"
    "- pages_max for phrases like 'under N pages', 'less than N pages', 'no more than N pages', 'max N pages', 'up to N pages' (INCLUSIVE - use the exact number N)\n"
    "IGNORE exact page requests like 'exactly N pages', 'N pages', 'around N pages' - books don't have exact page counts since they vary by edition.\n"
    "Examples:\n"
    "- 'over 250 pages' → pages_min: 250 (inclusive)\n"
    "- 'at least 200 pages' → pages_min: 200\n"
    "- 'under 300 pages' → pages_max: 300 (inclusive)\n"
    "- 'books with 400 pages' → all null (ignore exact)\n"
    "- 'exactly 350 pages' → all null (ignore exact)\n"
    "- 'around 180 pages' → all null (ignore exact)\n"
    "- 'over 250' (no 'pages' word) → all null\n"
    "- 'books about space' (no page numbers) → all null\n"
    "CRITICAL: Must contain both a number AND the word 'page'/'pages'. Only extract ranges (min/max), never exact values."
)
def extract_pages(query: str) -> Dict[str, Optional[int]]:
    out = _so(query, _PAGES_SYS, _PAGES_SCHEMA)
    return {
        "pages_min": out["pages_min"], 
        "pages_max": out["pages_max"]
    }

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
    "Return JSON for the schema. Extract numeric published year constraints if explicitly stated:\n"
    "- published_year_min for phrases like 'published after N', 'written after N', 'published from N', 'N or later', 'since N' (INCLUSIVE of N)\n"
    "- published_year_max for phrases like 'published before N', 'written before N', 'published up to N', 'published until N', 'no later than N' (INCLUSIVE of N)\n"
    "- published_year_exact for phrases like 'published in N', 'written in N', 'N edition', 'from N' (when referring to specific year)\n"
    "IMPORTANT: Only extract year constraints that explicitly mention publishing/writing context.\n"
    "IGNORE famous book titles with numbers like:\n"
    "- '1984' (George Orwell novel title, not publication year)\n"
    "- '2001' (A Space Odyssey title, not publication year)\n"
    "- 'Fahrenheit 451', 'Catch-22', 'Slaughterhouse-Five', etc.\n"
    "- Any number that appears to be part of a book title rather than publication context\n"
    "Examples:\n"
    "- 'books published in 2020' → published_year_exact: 2020\n"
    "- '1984 by George Orwell' → all null (book title, not publication year)\n"
    "- 'published after 2000' → published_year_min: 2001 (exclusive becomes inclusive)\n"
    "- 'written from 1990' → published_year_min: 1990\n"
    "- 'published before 2010' → published_year_max: 2009 (exclusive becomes inclusive)\n"
    "- 'published up to 2015' → published_year_max: 2015\n"
    "- '2001: A Space Odyssey' → all null (book title, not publication year)\n"
    "- 'up to 2010' (without publication context) → published_year_max: 2010\n"
    "Handle exclusive vs inclusive language carefully. If not stated, set to null."
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
        "properties": {"genre": {"type": ["string", "null"], "enum": ["Fiction", "Nonfiction", None]}},
        "required": ["genre"]
    }
}
_GENRE_SYS = (
    "Return JSON for the schema. Map genre-related terms to one of the specific enum values: "
    "Fiction, Nonfiction. "
    "Examples of mapping with HIGH CONFIDENCE:\n"
    "- 'fiction', 'novel', 'story', 'sci-fi', 'fantasy', 'romance', 'mystery', 'thriller', 'horror' → 'Fiction'\n"
    "- 'non-fiction', 'nonfiction', 'biography', 'memoir', 'history', 'self-help', 'textbook', 'manual' → 'Nonfiction'\n"
    "- 'autobiography', 'documentary', 'guide', 'cookbook', 'reference', 'encyclopedia' → 'Nonfiction'\n"
    "- 'science fiction', 'historical fiction', 'young adult fiction' → 'Fiction'\n"
    "Only return a value if you can map with HIGH CONFIDENCE to Fiction or Nonfiction. "
    "If ambiguous, vague, or no clear genre detected, return null. "
    "Output must be exactly 'Fiction' or 'Nonfiction' (case sensitive)."
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
    "Return JSON for the schema. Set children=true ONLY if the user is specifically looking for books "
    "INTENDED FOR children/kids to read (children's literature, kids' books, young readers). "
    "Require HIGH CONFIDENCE based on explicit user intent, do NOT infer from book titles alone.\n"
    "Examples that should be TRUE:\n"
    "- 'books for kids', 'children's books', 'kids' stories', 'young readers'\n"
    "- 'picture books', 'books for my 8-year-old', 'elementary school reading'\n"
    "Examples that should be FALSE:\n"
    "- 'books about children' (about children but not for children)\n"
    "- 'Children of the Corn', 'missing children story' (mentions children in title/plot)\n"
    "- 'Charlie and the Chocolate Factory' (just a title, no explicit intent for children)\n"
    "- 'parenting books', 'child psychology' (for adults about children)\n"
    "Only return true with HIGH CONFIDENCE if user explicitly wants books FOR children to read. "
    "If just mentioning a title or unclear intent, return false."
)
def extract_children(query: str) -> bool:
    out = _so(query, _CHILDREN_SYS, _CHILDREN_SCHEMA)
    return out["children"]

# -----------------------
# 5) Keywords Extraction (exact phrases)
# -----------------------
_KEYWORDS_SCHEMA = {
    "name": "KeywordsExtraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["keywords"]
    }
}
_KEYWORDS_SYS = (
    "Return JSON for the schema. Extract meaningful entities and noun phrases from the query with HIGH CONFIDENCE. "
    "Focus on:\n"
    "1. ENTITIES: proper names (places, regions, countries, cities, planets, nationalities, historical events, decades)\n"
    "2. TOPICS: significant themes, concepts, objects, subjects (NOT genre categories)\n"
    "3. NOUN PHRASES: meaningful descriptive terms\n\n"
    "Examples of what TO EXTRACT:\n"
    "- Places: 'New York', 'Mars', 'Victorian England', 'France'\n"
    "- Events: 'World War II', 'Cold War', 'Renaissance'\n" 
    "- Decades: '1980s', '1960s' (when referring to time period/era)\n"
    "- Specific topics: 'dragons', 'artificial intelligence', 'space exploration', 'detective work'\n"
    "- Concepts: 'terraforming', 'first contact', 'time travel', 'vampire mythology'\n"
    "- Activities: 'colonization', 'ethics', 'mythology'\n\n"
    "EXCLUDE with HIGH CONFIDENCE:\n"
    "- Filler words: a, an, the, and, or, but, with, about, for, in, on, at, I, you, want, need, looking\n"
    "- Generic book terms: book, books, novel, novels, story, stories, fiction, nonfiction, literature, reading\n"
    "- Page constraints: pages, page, under, over, at least, no more than, any number + pages\n"
    "- Publication years: 1990, 2010, 2000 (when used for 'published in/after/before')\n"
    "- Famous book title numbers: '1984', '2001', '451', '22', '39', '5', '7' (from titles like '1984', '2001: A Space Odyssey', 'Fahrenheit 451', 'Catch-22', etc.)\n"
    "- Tone/emotion: happy, sad, scary, fear, joy, anger, neutral, horror, uplifting, depressing\n"
    "- Genre categories: mystery, romance, thriller, fantasy, science fiction, horror (these are handled separately)\n"
    "- Generic verbs: is, are, was, were, have, has, had, do, does, did, can, could, would\n"
    "- Children terms: children, kids, child (when referring to target audience)\n"
    "- Author names: ANY author names are handled separately, NEVER include them\n"
    "- Book titles: if query appears to be just a book title with author, extract ONLY meaningful content topics\n"
    "- Any terms that match existing filters in context.existing_filters\n\n"
    "IMPORTANT: If context.existing_filters contains authors, do NOT extract any author names. "
    "If it contains genre info, focus only on content topics, not genre terms. "
    "Only extract entities and specific topics that exist EXACTLY in the query and are NOT already captured. "
    "Preserve original casing. If no meaningful entities or topics found, return empty list."
)
def extract_keywords(query: str, filters: Dict[str, Any] = None) -> List[str]:
    # Pass existing filters as context to avoid duplication
    extra_context = {"existing_filters": filters or {}}
    out = _so(query, _KEYWORDS_SYS, _KEYWORDS_SCHEMA, extra=extra_context)
    return out["keywords"]

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
    author = extract_authors(query)

    years = extract_published_year(query)

    filters: Dict[str, Any] = {}
    if tone: filters["tone"] = tone
    if pages.get("pages_min") is not None: filters["pages_min"] = pages["pages_min"]
    if pages.get("pages_max") is not None: filters["pages_max"] = pages["pages_max"]
    if genre: filters["genre"] = genre
    if child: filters["children"] = True
    if author: filters["author"] = author

    # Only add published_year if at least one value is not None
    if any(value is not None for value in years.values()):
        filters["published_year"] = years

    keywords = extract_keywords(query, filters)
    # clean the keywords and make sure that it's good
    # remove_keywords_duplicates(keywords, filters)
    if keywords: 
        filters["keywords"] = keywords

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
            