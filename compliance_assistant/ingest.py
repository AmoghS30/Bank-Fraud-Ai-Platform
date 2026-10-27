"""
Stage 4 — Document Ingestion
Loads regulatory text documents, chunks them, embeds with sentence-transformers,
and stores in a local ChromaDB vector store.

Run once: python3 compliance_assistant/ingest.py
Safe to re-run — collection is cleared and rebuilt.
"""

import os
from pathlib import Path

from chromadb import PersistentClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings

import os as _os
_os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")  # Allow download on first run

DOCS_DIR = "compliance_assistant/documents"
VECTOR_DIR = "compliance_assistant/vector_store"
COLLECTION_NAME = "regulatory_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def ingest():
    print(f"Loading documents from {DOCS_DIR}/...")
    loader = DirectoryLoader(
        DOCS_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"  Loaded {len(docs)} document(s)")

    # Chunk at paragraph/section boundaries
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n=====", "\n-----", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"  Split into {len(chunks)} chunks (avg {sum(len(c.page_content) for c in chunks)//len(chunks)} chars)")

    print(f"\nEmbedding with {EMBED_MODEL}...")
    embedder = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Build ChromaDB collection
    os.makedirs(VECTOR_DIR, exist_ok=True)
    client = PersistentClient(path=VECTOR_DIR)

    # Delete and recreate for clean rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    texts = [c.page_content for c in chunks]
    sources = [c.metadata.get("source", "unknown") for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embeddings = embedder.embed_documents(batch_texts)
        collection.add(
            ids=ids[i : i + batch_size],
            documents=batch_texts,
            embeddings=batch_embeddings,
            metadatas=[{"source": s} for s in sources[i : i + batch_size]],
        )
        print(f"  Indexed {min(i + batch_size, len(texts))}/{len(texts)} chunks", end="\r")

    print(f"\n  Done. {collection.count()} chunks in vector store → {VECTOR_DIR}/")


if __name__ == "__main__":
    ingest()
