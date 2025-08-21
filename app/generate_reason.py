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
        temperature=0.7,  # Increased for more creative, conversational responses
        max_tokens=250,   # Limit response length for concise explanations
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
        "properties": {"explanation": {"type": "string"}},
        "required": ["explanation"]
    }
}
_EXPLAIN_OVERALL_SYS = (
    "You are a friendly book recommendation assistant that explains the filtering process to users.\n\n"
    
    "TASK: Create a conversational, encouraging summary of how we found books matching the user's request.\n\n"
    
    "INPUT: You'll receive filtering steps in this format:\n"
    "{'applied_author': 'Applied authors=[...]: narrowed X → Y books.', 'applied_genre': '...', etc.}\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Analyze the filtering progression step by step\n"
    "2. Write in a warm, conversational tone (use 'I', 'we', 'your')\n"
    "3. Emphasize the positive outcome - finding books that match their criteria\n"
    "4. Mention the key filters applied (author, genre, pages, keywords, etc.)\n"
    "5. Show how we narrowed down from many books to perfect matches\n"
    "6. Keep it concise but engaging (2-4 sentences)\n\n"
    
    "EXAMPLE STYLE:\n"
    "- 'Great! I found some excellent matches for your request...'\n"
    "- 'Perfect! Starting with our collection of X books, I first looked for...'\n"
    "- 'Wonderful! After applying your filters, we've found Y books that...'\n\n"
    
    "AVOID:\n"
    "- Technical jargon or database terms\n"
    "- Dry, robotic language\n"
    "- Negative framing ('only X books left')\n"
    "- Overly long explanations\n\n"
    
    "Focus on making the user feel confident that we found great books tailored to their specific interests."
)

def explain_overall_recommendation(messages_logs: dict) -> str:
    # Generate an explanation for the overall recommendation
    # Convert dictionary to JSON string for AI analysis
    content = json.dumps(messages_logs, ensure_ascii=False)
    
    try:
        out = _so_overall(content, _EXPLAIN_OVERALL_SYS, _EXPLAIN_OVERALL_SCHEMA)    
        message = out.get("explanation", "Sorry, I couldn't summarize my filter process, but here are some great books for you!")
    except Exception as e:
        print(f"Error generating explanation: {e}")
        message = "Sorry, I had trouble summarizing the filter process."

    return message


# -----------------------
# 2) explain why there are no books
# -----------------------

_EXPLAIN_NO_BOOKS_SYS = (
    "You are a friendly book recommendation assistant that helps users understand why no books were found for their request.\n\n"
    
    "TASK: Create a helpful, encouraging explanation of why we couldn't find books matching the user's criteria.\n\n"
    
    "INPUT: You'll receive filtering steps in this format:\n"
    "{'applied_author': 'Applied authors=[...]: narrowed X → Y books.', 'applied_genre': '...', etc.}\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Analyze the filtering progression to identify where it became too restrictive\n"
    "2. Write in a warm, supportive tone (use 'I', 'we', 'your')\n"
    "3. Gently suggest what might be causing the issue without being critical\n"
    "4. Provide specific, actionable suggestions for finding books\n"
    "5. Stay positive and encouraging throughout\n"
    "6. Keep it concise but helpful (2-4 sentences)\n\n"
    
    "COMMON ISSUES TO ADDRESS:\n"
    "- Author/keyword combinations: 'Please double-check your spelling of author names or keywords'\n"
    "- Numeric filters (pages): 'Make sure these page numbers are reasonable for your search'\n"
    "- Too many filters: 'Try removing one or two filters to broaden your search'\n"
    "- Specific combinations: 'This particular combination might be too specific'\n\n"
    
    "EXAMPLE STYLE:\n"
    "- 'I couldn't find any books matching those exact criteria, but let me help you adjust your search...'\n"
    "- 'It looks like your search was quite specific. Try double-checking the spelling or...'\n"
    "- 'No matches found, but don't worry! Let's try making your search a bit broader by...'\n\n"
    
    "AVOID:\n"
    "- Blaming the user or making them feel bad\n"
    "- Technical jargon or error messages\n"
    "- Negative language like 'failed', 'wrong', 'impossible'\n"
    "- Overly complex explanations\n\n"
    
    "Focus on being helpful and encouraging while guiding them toward a successful search."
)

def explain_no_books_found(messages_logs: dict) -> str:
    # Generate an explanation for why there are no books
    # Convert dictionary to JSON string for AI analysis
    content = json.dumps(messages_logs, ensure_ascii=False)
    
    try:
        out = _so_overall(content, _EXPLAIN_NO_BOOKS_SYS, _EXPLAIN_OVERALL_SCHEMA)            
        message = out.get("explanation", "Sorry, I couldn't summarize my filter process, but here are some great books for you!")
    except Exception as e:
        print(f"Error generating explanation: {e}")
        message = "Sorry, I had trouble summarizing the filter process."

    return message


# -----------------------
# 3) give a smaller prompts if there are no filter
# -----------------------

_EXPLAIN_NO_FILTERS = (
    "You are a friendly book recommendation assistant that introduces book recommendations to users.\n\n"
    
    "TASK: Create a warm, welcoming introduction for presenting book recommendations.\n\n"
    
    "INPUT: You'll receive the user's original request/query as a string.\n\n"
    
    "INSTRUCTIONS:\n"
    "1. Acknowledge the user's request in a friendly way\n"
    "2. Use a warm, conversational tone (use 'I', 'we', 'your')\n"
    "3. Express enthusiasm about the recommendations you found\n"
    "4. Keep it brief and welcoming (1-2 sentences)\n"
    "5. Transition smoothly to presenting the books\n\n"
    
    "EXAMPLE STYLE:\n"
    "- 'Here are some wonderful books based on your request for...'\n"
    "- 'I found some great recommendations for you! Based on your interest in...'\n"
    "- 'Perfect! Here are some fantastic books that match what you're looking for...'\n"
    "- 'Great choice! I've found some excellent books about...'\n\n"
    
    "AVOID:\n"
    "- Technical language or filter terminology\n"
    "- Overly long introductions\n"
    "- Mentioning specific numbers or filtering steps\n"
    "- Formal or robotic language\n\n"
    
    "Focus on making the user excited about the books you're about to show them."
)

def explain_no_filter_applied(user_query: str) -> str:
    # Generate a friendly introduction for book recommendations
    try:
        out = _so_overall(user_query, _EXPLAIN_NO_FILTERS, _EXPLAIN_OVERALL_SCHEMA)
        message = out.get("explanation", "Here are some great books based on your request!")
    except Exception as e:
        print(f"Error generating introduction: {e}")
        message = "Here are some wonderful books I found for you!"

    return message
