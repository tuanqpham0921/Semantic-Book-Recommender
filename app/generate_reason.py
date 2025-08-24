import json
import logging

# Get the logger (same configuration as main.py)
logger = logging.getLogger(__name__)

from app.models import (
    BookRecommendationResponse, BookRecommendation,
    FilterSchema
)
from app.config import client, MODEL

_MAX_CHAR = 250

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
        temperature=0.7,  # Increased for more creative, conversational responses
        max_tokens=75,    # Limit response length for concise explainations (1-2 sentences)
        top_p=0.9,        # Nucleus sampling for better quality
        frequency_penalty=0.1,  # Slight penalty to avoid repetition
        presence_penalty=0.1,   # Encourage varied vocabulary
    )
    return json.loads(resp.choices[0].message.content)

def get_response_messages(request: BookRecommendationResponse):
    validation_logs = request.validation
    messages_logs = {}
    for key, value in validation_logs.dict().items():
        if value is None: continue

        if value["num_books_before"] == value["num_books_after"]:
            continue

        if value["message"] and len(value["message"]) != 0:
            messages_logs[key] = value["message"]

    return messages_logs

# -----------------------
# 1) explain the overall schema
# -----------------------
_EXPLAIN_OVERALL_SCHEMA = {
    "name": "ExplainOverall",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"explaination": {"type": "string"}},
        "required": ["explaination"]
    }
}
_EXPLAIN_OVERALL_SYS = (
    "You are a friendly, helpful book recommendation assistant.\n\n"
    
    "TASK: Write a short, conversational summary explaining how we found books that match the user's request.\n\n"
    
    "INPUT FORMAT:\n"
    "{'applied_author': 'Applied authors=[...]: narrowed X → Y books.', 'applied_genre': '...', etc.}\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Summarize the filtering journey naturally, without listing every step\n"
    "2. Use a warm, encouraging tone ('I', 'we', 'your')\n"
    "3. Focus on the final result and how it aligns with what the user wanted\n"
    "4. Mention the most relevant filters (genre, length, author, keywords, etc.)\n"
    "5. Avoid sounding like a log or giving too many numbers\n"
    "6. Keep it short and upbeat – aim for 1–2 engaging sentences\n\n"
    
    "EXAMPLE STYLES:\n"
    "- 'We found some great picks that match your love for long, inspiring nonfiction.'\n"
    "- 'After narrowing things down by genre and tone, I found a solid list that fits just what you were looking for.'\n"
    "- 'Looks like we've got a great selection of books that hit all your criteria — genre, author, and even tone!'\n\n"
    
    "AVOID:\n"
    "- Listing each filter or step numerically\n"
    "- Too many stats ('went from X to Y') unless it feels very natural\n"
    "- Robotic or repetitive wording\n\n"
    "GOAL: Make the user feel confident and excited about their personalized results, without overwhelming them with process details."
)

def explain_overall_recommendation(messages_logs: dict) -> str:
    # Generate an explaination for the overall recommendation
    # Convert dictionary to JSON string for AI analysis
    content = json.dumps(messages_logs, ensure_ascii=False)
    
    try:
        out = _so_overall(content, _EXPLAIN_OVERALL_SYS, _EXPLAIN_OVERALL_SCHEMA)    
        message = out.get("explaination", "Sorry, I couldn't summarize my filter process, but here are some great books for you!")
    except Exception as e:
        print(f"Error generating explaination: {e}")
        message = "Sorry, I had trouble summarizing the filter process."

    return message[:_MAX_CHAR]


# -----------------------
# 2) explain why there are no books
# -----------------------

_EXPLAIN_NO_BOOKS_SYS = (
    "You are a warm, supportive book recommendation assistant who helps users adjust their search when no books are found.\n\n"
    
    "TASK: Write a short, encouraging explaination when no books matched the user's filters.\n\n"
    
    "INPUT FORMAT:\n"
    "{'applied_author': 'Applied authors=[...]: narrowed X → Y books.', 'applied_genre': '...', etc.}\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Briefly explain that no matches were found – keep it light and positive\n"
    "2. Gently suggest what might be the cause (e.g., spelling, too many filters, rare combo)\n"
    "3. Offer 1–2 specific suggestions to improve the search (e.g., remove filters, adjust range)\n"
    "4. Write in a calm, encouraging tone using 'you', 'let’s', 'how about'\n"
    "5. Keep it short and chat-friendly — 1 to 2 sentences max\n\n"
    
    "EXAMPLE OUTPUT:\n"
    "- 'Hmm, looks like nothing matched those exact filters. How about trying fewer keywords or widening the page range?'\n"
    "- 'I couldn’t find anything just yet, but we can fix that — maybe try a broader genre or double-check any author spelling?'\n"
    "- 'Your search is super specific (which is awesome!), but loosening one or two filters might help us find something great.'\n\n"
    
    "AVOID:\n"
    "- Blaming or overwhelming the user\n"
    "- Sounding robotic, technical, or too apologetic\n"
    "- Listing every failed filter step\n\n"
    "GOAL: Make the user feel supported and motivated to adjust their search — like a helpful librarian, not a system error."
)

def explain_no_books_found(messages_logs: dict) -> str:
    # Generate an explaination for why there are no books
    # Convert dictionary to JSON string for AI analysis
    content = json.dumps(messages_logs, ensure_ascii=False)
    
    try:
        out = _so_overall(content, _EXPLAIN_NO_BOOKS_SYS, _EXPLAIN_OVERALL_SCHEMA)            
        message = out.get("explaination", "Sorry, I couldn't summarize my filter process, but here are some great books for you!")
    except Exception as e:
        print(f"Error generating explaination: {e}")
        message = "Sorry, I had trouble summarizing the filter process."

    return message[:_MAX_CHAR]


# -----------------------
# 3) give a smaller prompts if there are no filter
# -----------------------

_EXPLAIN_NO_FILTERS = (
    "You are a friendly and enthusiastic book recommendation assistant.\n\n"
    
    "TASK: Write a short, warm introduction when presenting book recommendations based on the user's query.\n\n"
    
    "INPUT:\n"
    "A single string containing the user’s original request (e.g., 'books about adventure in space').\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Acknowledge the request in a cheerful, conversational tone (use 'I', 'we', 'your')\n"
    "2. Express excitement about sharing some great books\n"
    "3. Keep it natural and brief – aim for 1 sentence, 2 at most\n"
    "4. Avoid technical or formal language (no 'filters', 'retrieval', etc.)\n"
    "5. End with a smooth lead-in to showing book results\n\n"
    
    "EXAMPLE OUTPUTS:\n"
    "- 'I found some awesome books about adventure in space — I think you’ll love these!'\n"
    "- 'Great choice! Here are some exciting reads that match your request.'\n"
    "- 'Let’s dive in! I picked out some fantastic books based on what you're looking for.'\n"
    "- 'These recommendations are right up your alley — let’s take a look!'\n\n"
    
    "AVOID:\n"
    "- Mentioning filter steps or how the books were found\n"
    "- Overexplaining the process\n"
    "- Sounding robotic or generic\n\n"
    "GOAL: Make the user feel welcomed, excited, and ready to explore the book recommendations you're about to share."
)

def explain_no_filter_applied(user_query: str) -> str:
    # Generate a friendly introduction for book recommendations
    try:
        out = _so_overall(user_query, _EXPLAIN_NO_FILTERS, _EXPLAIN_OVERALL_SCHEMA)
        message = out.get("explaination", "Here are some great books based on your request!")
    except Exception as e:
        print(f"Error generating introduction: {e}")
        message = "Here are some wonderful books I found for you!"

    return message[:_MAX_CHAR]

# -----------------------------------------------------------------------------

def get_book_filter_messages(book: BookRecommendation, filters: FilterSchema) -> dict:
    """
    Generates messages for a single book based on how it matches the provided filters.

    This function checks a book against various filter criteria (author, pages, year, etc.)
    and creates a dictionary of human-readable strings for each criterion that matches.

    Args:
        book: The book object to be evaluated.
        filters: The schema containing all active filter criteria.

    Returns:
        A dictionary where each key is a matched filter (e.g., 'matched_author')
        and the value is a string explaining why the book matched that filter.
    """
    result = {}

    if filters.author and book.authors:
        book_authors_lower = book.authors.lower()
        # Check if any of the filter authors match the book's authors
        matching_authors = [author for author in filters.author if author.lower() in book_authors_lower]
        if matching_authors:
            result["matched_author"] = f"The book is by {book.authors}, which matches your author filter for {', '.join(matching_authors)}."

    if filters.pages_min and book.num_pages and book.num_pages >= filters.pages_min:
        result["matched_min_pages"] = f"The book has {book.num_pages} pages, which meets your minimum page count filter of {filters.pages_min}."

    if filters.pages_max and book.num_pages and book.num_pages <= filters.pages_max:
        result["matched_max_pages"] = f"The book has {book.num_pages} pages, which meets your maximum page count filter of {filters.pages_max}."

    if filters.published_year and book.published_year:
        if filters.published_year.get("min") and book.published_year >= filters.published_year["min"]:
            result["matched_min_published_year"] = f"The book was published in {book.published_year}, which meets your minimum published year filter of {filters.published_year['min']}."
        if filters.published_year.get("max") and book.published_year <= filters.published_year["max"]:
            result["matched_max_published_year"] = f"The book was published in {book.published_year}, which meets your maximum published year filter of {filters.published_year['max']}."
        if filters.published_year.get("exact") and filters.published_year["exact"] == book.published_year:
            result["matched_exact_published_year"] = f"The book was published in {book.published_year}, which exactly matches your published year filter of {filters.published_year['exact']}."

    genre = ""
    if filters.children:
        genre = "Children's "
        result["matched_children"] = "You requested Children's books."

    if filters.genre and filters.genre in ["Fiction", "Nonfiction"]:
        genre = [genre + filters.genre]
    else:
        genre = ["Children's Fiction", "Children's Nonfiction"]

    if book.simple_categories and book.simple_categories in genre:
        result["matched_genre_categories"] = f"The book belongs to the {book.simple_categories} category(ies), which matches your genre {', '.join(genre)}."

    if filters.keywords and book.description:
        matching_keywords = [kw for kw in filters.keywords if kw.lower() in book.description.lower()]
        if matching_keywords:
            result["matched_keywords"] = f"The book's description matches your keywords: {', '.join(matching_keywords)}."

    if filters.keywords and book.title:
        matching_title = [kw for kw in filters.keywords if kw.lower() in book.title.lower()]
        if matching_title:
            result["matched_title"] = f"The book's title matches your keywords: {', '.join(matching_title)}."

    if filters.tone:
        tone_score = getattr(book, filters.tone, None)
        if tone_score:
            result["matched_tone"] = f"The book has a {filters.tone} tone score of {str(tone_score)[:5]} out of 1.0"

    return result

_EXPLAIN_BOOK_RECOMMENDATION = (
    "You are a friendly and enthusiastic book recommendation assistant.\n\n"
    
    "TASK: Write a short, engaging summary explaining why a specific book is a great match for the user.\n\n"
    
    "INPUT FORMAT:\n"
    "A dictionary of reasons the book matched, like:\n"
    "{'matched_author': 'Book is by an author you like.', 'matched_keywords': 'Description matches keywords.', 'matched_tone': 'Book has the right tone.'}\n\n"
    
    "CONTEXT:\n"
    "The user's original query will also be provided for additional context.\n\n"

    "INSTRUCTIONS:\n"
    "1. Weave the reasons from the input dictionary into a natural, conversational sentence.\n"
    "2. Use a warm, positive, and encouraging tone. Make it sound like a personal recommendation.\n"
    "3. Highlight 1-2 of the most important matching points (like author, keywords, or tone).\n"
    "4. Keep it concise and exciting – aim for 1-2 sentences.\n"
    "5. Start by saying why this specific book is a great choice.\n\n"

    "EXAMPLE OUTPUTS:\n"
    "- 'I think you’ll really enjoy this one! It’s a perfect fit for the genre you were looking for and has that adventurous tone you wanted.'\n"
    "- 'This seems like just the book for you! It’s by an author you were interested in and the story hits on several of your keywords.'\n"
    "- 'Based on your request, this is a fantastic match. It has the perfect page count and the uplifting, hopeful feel you asked for.'\n\n"

    "AVOID:\n"
    "- Simply listing the reasons from the dictionary (e.g., 'Matched author. Matched keywords.').\n"
    "- Sounding robotic or like a system log.\n"
    "- Being generic. Connect directly to the user's known preferences.\n\n"
    
    "GOAL: Make the user feel like this book was hand-picked just for them, building excitement and trust in the recommendation."
)

def explain_book_recommendation(book: BookRecommendation, filters: FilterSchema, content: str) -> str:
    # Generate an explaination for the book recommendation
    logger.info(f"*** in explain_book_recommendation")
    messages = get_book_filter_messages(book, filters)

    logger.info(f"*** Finished get_book_filter_messages")
    logger.info(f"Messages: {messages}")
    logger.info(f"=======================================")

    # TODO: Need to make sure that even tho there are no messages
    # we still provide a meaningful explanation, because of the similarity search
    # we recommended for a reason. We can provide generic explanations. or use messages as extra
    if not messages:
        message = f"Sorry, there's no messages for {book.title}"
        return message

    logger.info(f"*** QUERYing _so_overall")
    try:
        out = _so_overall(messages, _EXPLAIN_BOOK_RECOMMENDATION, _EXPLAIN_OVERALL_SCHEMA, content)
        message = out.get("explaination", f"Sorry, I had trouble explaining why I recommended this {book.title}. But this is a good match for you")
    except Exception as e:
        print(f"Error generating book explaination: {e}")
        message = f"Sorry, I had trouble explaining why I recommended this {book.title}. There was an error when getting the book explanation"

    logger.info(f"*** Finished explain_book_recommendation")
    return message[:_MAX_CHAR]