import os
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

def create_chroma_db(tagged_descriptions_path: str = "data/tagged_descriptions.txt", persist_directory: str = "./chroma_db"):
    print("Starting ChromaDB creation...")

    raw_documents = TextLoader(file_path=tagged_descriptions_path).load()
    seen_line = set()
    documents = []

    for doc in raw_documents:
        lines = doc.page_content.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            match = re.match(r'^(\d+)', stripped)
            isbn = match.group(1) if match else None

            if stripped not in seen_line:
                metadata = {"source": tagged_descriptions_path}
                if isbn:
                    metadata["isbn"] = isbn
                documents.append(Document(page_content=stripped, metadata=metadata))
                seen_line.add(stripped)

    print(f"Created {len(documents)} unique documents.")

    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    db_books = Chroma.from_documents(
        documents,
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
        persist_directory=persist_directory
    )
    print(f"ChromaDB created and saved at {persist_directory}")

if __name__ == "__main__":
    create_chroma_db()
