import json
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

_EXPLAIN_BOOK_RECOMMENDATION = (
    "You are a friendly and enthusiastic book recommendation assistant.\n\n"
    
)

def explain_book_recommendation(book: BookRecommendation, filters: FilterSchema, content: str) -> str:
    # Generate an explaination for the book recommendation
    payload = {**book.dict(), **filters.dict()}

    try:
        out = _so_overall(payload, _EXPLAIN_BOOK_RECOMMENDATION, _EXPLAIN_OVERALL_SCHEMA, content)
        message = out.get("explaination", "Here’s a great book I found for you!")
    except Exception as e:
        print(f"Error generating book explaination: {e}")
        message = "I had trouble explaining the book recommendation."

    return message[:_MAX_CHAR]