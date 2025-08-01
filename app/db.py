from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import OPENAI_API_KEY, CHROMA_DB_PATH

def get_chroma_db():
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    )
