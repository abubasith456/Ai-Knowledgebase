import os
from typing import List, Optional
from loguru import logger
import chromadb

try:
    from .embeddings import get_embedding_function
    from .schemas import QueryResponse, RetrievedContext
except ImportError:
    from embeddings import get_embedding_function
    from schemas import QueryResponse, RetrievedContext


def _client() -> chromadb.Client:
    host = os.environ.get("CHROMA_HOST")
    if host:
        return chromadb.HttpClient(host=host, port=int(os.environ.get("CHROMA_PORT", "8000")))
    else:
        from pathlib import Path
        from chromadb.config import Settings
        data_dir = Path(os.environ.get("CHROMA_DATA_DIR") or (Path.cwd() / "data" / "chroma"))
        data_dir.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(data_dir))

 

def _synthesize_answer(question: str, contexts: List[str]) -> str:
    header = f"Question: {question}\n\n"
    body = "\n\n".join(contexts[:3])
    return header + body


def query_knowledgebase(x_api_key: str, question: str, top_k: int = 5, index_id: Optional[str] = None) -> QueryResponse:
    client = _client()
    user_key = str(abs(hash(x_api_key)))[:10]
    user_prefix = os.environ.get("COLLECTION_PREFIX", "kb_") + user_key + "_"
    collections = client.list_collections()
    
    if index_id:
        # Query specific index
        index_collection_name = f"{user_prefix}index_{index_id}"
        user_collections = [c for c in collections if getattr(c, 'name', '') == index_collection_name]
    else:
        # Query all user collections (legacy behavior)
        user_collections = [c for c in collections if getattr(c, 'name', '').startswith(user_prefix)]

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