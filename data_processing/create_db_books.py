import numpy as np
import pandas as pd
from dotenv import load_dotenv
import re
import os

# Load the CSV file into a pandas DataFrame
# books = pd.read_parquet('data/books.parquet')
# print("Column names:")
# print(books.columns.tolist())
# print("=" * 100)


# # stuff with the thumbnail and picture sizes

# books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
# books["large_thumbnail"] = np.where(
#     books["large_thumbnail"].isna(),
#     "data/cover-not-found.jpg",
#     books["large_thumbnail"],
# )

# Save the DataFrame to a new CSV file
# books.to_csv('data/books_with_emotions_test.csv', index=False)

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

raw_documents = TextLoader(file_path = "tagged_descriptions.txt").load()
seen_line = set()
documents = []

for doc in raw_documents:
  lines = doc.page_content.split("\n")
  for line in lines:
    stripped = line.strip()
    if not stripped:
      continue

    # Extract ISBN from the beginning of the line
    # Assuming ISBN is a sequence of digits at the start
    # Use regex to find the first sequence of digits
    match = re.match(r'^(\d+)', stripped)
    isbn = None
    if match:
      isbn = match.group(1)

    # Check if the full line (which should be unique per book) has been seen
    # Or alternatively, if the extracted ISBN has been seen
    # Let's deduplicate by the full stripped line content to keep unique descriptions
    if stripped not in seen_line:
      # Store the extracted ISBN in metadata if found
      metadata = {"source": "tagged_descriptions.txt"}
      if isbn:
          metadata["isbn"] = isbn # Store as "isbn" in metadata

      documents.append(Document(page_content=stripped, metadata=metadata))
      seen_line.add(stripped) # Deduplicate based on the full stripped line

print(f"Created {len(documents)} documents after de-duplication.")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

db_books = Chroma.from_documents(
    documents,
    embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
    persist_directory="data/chroma_db"  # Choose a folder name
)
print("Database created with Chroma.")