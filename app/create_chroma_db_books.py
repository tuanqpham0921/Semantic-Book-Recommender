import re
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, CHROMA_DB_PATH, TAGGED_DESCRIPTIONS_PATH

def create_chroma_db(tagged_descriptions_path: str = TAGGED_DESCRIPTIONS_PATH, persist_directory: str = CHROMA_DB_PATH):
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

    db_books = Chroma.from_documents(
        documents,
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
        persist_directory=persist_directory
    )
    print(f"ChromaDB created and saved at {persist_directory}")

if __name__ == "__main__":
    create_chroma_db()
