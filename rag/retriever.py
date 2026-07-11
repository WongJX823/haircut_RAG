"""
Loads the FAISS index and retrieves relevant haircut knowledge chunks.
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

INDEX_DIR = "knowledge_base/index"
_vectorstore = None


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _vectorstore = FAISS.load_local(
            INDEX_DIR, embeddings, allow_dangerous_deserialization=True
        )
    return _vectorstore


def retrieve_chunks(query: str, k: int = 4) -> list[str]:
    vs = get_vectorstore()
    docs = vs.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]
