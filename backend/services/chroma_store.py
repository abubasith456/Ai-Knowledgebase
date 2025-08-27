import chromadb
from typing import List, Dict, Any, Optional

# New persistent local client API
_client = chromadb.PersistentClient(path="./chroma")


def get_or_create_collection(name: str):
    return _client.get_or_create_collection(name=name)


def add_documents(
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    documents: Optional[List[str]] = None,
):
    col = get_or_create_collection(collection_name)
    col.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
