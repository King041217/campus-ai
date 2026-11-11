"""Vector Store - ChromaDB native, role-separated collections"""
import os
import chromadb
from chromadb.config import Settings
from typing import List
from langchain_core.documents import Document
from .embeddings import get_embeddings

#Large Persistence directory
_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
_client = None
_collection = None

def _get_collection_for_role(role: str):
    global _client, _collection
    if _collection is not None and getattr(_collection, "_role", None) == role:
        return _collection
    _client = chromadb.PersistentClient(path=_PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
    name = f"campus_knowledge_{role}"
    _collection = _client.get_or_create_collection(
        name=name,
        embedding_function=get_embeddings()
    )
    return _collection

def get_vector_store(role: str = "student"):
    return _get_collection_for_role(role)

def add_documents(docs: List[Document], role: str = "student") -> int:
    col = _get_collection_for_role(role)
    ids = [str(i) + "_" + os.urandom(4).hex() for i in range(len(docs))]
    col.add(ids=ids, documents=[d.page_content for d in docs], metadatas=[d.metadata for d in docs])
    return len(docs)

def reset_store(role: str = "student") -> None:
    global _collection
    client = chromadb.PersistentClient(path=_PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
    name = f"campus_knowledge_{role}"
    try:
        client.delete_collection(name)
    except Exception:
        pass
    _collection = None

def get_store_info(role: str = "student") -> dict:
    col = _get_collection_for_role(role)
    return {"collection_name": f"campus_knowledge_{role}", "document_count": col.count(), "persist_directory": _PERSIST_DIR}
