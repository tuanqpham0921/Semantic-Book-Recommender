import requests
url = "http://localhost:8000/recommend_books"
headers = {"Content-Type": "application/json"}
#===================================================================
prompts = [
    "a book about forgiveness",
    "a 300 page or more books by Stephen King with a sad tone and take place in Maine",
    "get me books by Stephen King and J.K. Rowling"
]
#===================================================================
# PROMPT = " "
PROMPT = prompts[0] 
#===================================================================

payload = {
    "description": PROMPT
}

response = requests.post(url, json=payload, headers=headers)

#===================================================================

if not response.ok:
    print(f"Error {response.status_code}: {response.text}")
    quit()

result = response.json()

for book in result:
    print(f"{book['title']} - {book['authors']} - {book['num_pages']} pages")
    print("-------------------------\n")