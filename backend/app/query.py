# Disable ChromaDB telemetry globally
import os
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

from typing import List, Optional
from loguru import logger
import chromadb

try:
    from .embeddings import get_embedding_function
    from .schemas import QueryResponse, RetrievedContext
    from .chroma_client import get_chroma_client
except ImportError:
    from embeddings import get_embedding_function
    from schemas import QueryResponse, RetrievedContext
    from chroma_client import get_chroma_client


def _client() -> chromadb.Client:
    """Get ChromaDB client with telemetry disabled."""
    return get_chroma_client()

 

def _synthesize_answer(question: str, contexts: List[str]) -> str:
    header = f"Question: {question}\n\n"
    body = "\n\n".join(contexts[:3])
    return header + body


def query_knowledgebase(question: str, top_k: int = 5, index_id: Optional[str] = None) -> QueryResponse:
    client = _client()
    prefix = os.environ.get("COLLECTION_PREFIX", "kb_")
    collections = client.list_collections()
    
    if index_id:
        # Query specific index
        index_collection_name = f"{prefix}index_{index_id}"
        user_collections = [c for c in collections if getattr(c, 'name', '') == index_collection_name]
    else:
        # Query all collections (legacy behavior)
        user_collections = [c for c in collections if getattr(c, 'name', '').startswith(prefix)]

    if not user_collections:
        return QueryResponse(answer="No documents ingested yet." + (f" Index '{index_id}' not found." if index_id else ""), contexts=[])

    embedder = get_embedding_function()
    q_emb = embedder([question])[0]

    all_results: List[RetrievedContext] = []
    for collection in user_collections:
        try:
            res = collection.query(query_embeddings=[q_emb], n_results=top_k)
            ids = res.get('ids', [[]])[0]
            docs = res.get('documents', [[]])[0]
            dists = res.get('distances', [[]])[0]
            metas = res.get('metadatas', [[]])[0]
            for i, doc in enumerate(docs):
                score = float(dists[i]) if i < len(dists) else 0.0
                ctx = RetrievedContext(
                    chunk_id=ids[i],
                    score=score,
                    text=doc,
                    metadata=metas[i] if i < len(metas) and isinstance(metas[i], dict) else {},
                )
                all_results.append(ctx)
        except Exception as exc:
            logger.warning(f"Query failed for collection {getattr(collection, 'name', '')}: {exc}")
            continue

    all_results.sort(key=lambda c: c.score)
    top_contexts = all_results[:top_k]
    answer = _synthesize_answer(question, [c.text for c in top_contexts])
    return QueryResponse(answer=answer, contexts=top_contexts)