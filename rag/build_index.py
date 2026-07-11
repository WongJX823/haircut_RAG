"""
Loads haircut documents from knowledge_base/docs,
splits them into chunks, embeds with OpenAI, and saves a FAISS index.
Run once: python -m rag.build_index
"""

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

DOCS_DIR = "knowledge_base/docs"
INDEX_DIR = "knowledge_base/index"


def build_index():
    print("Loading documents...")
    loader = DirectoryLoader(
        DOCS_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    if not docs:
        raise ValueError(f"No documents found in {DOCS_DIR}. Add .txt haircut guides first.")

    print(f"Loaded {len(docs)} document(s). Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("Embedding and building FAISS index...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)
    print(f"Index saved to {INDEX_DIR}/")


if __name__ == "__main__":
    build_index()
