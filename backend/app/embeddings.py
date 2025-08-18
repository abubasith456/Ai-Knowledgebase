import os
from typing import Callable, List
from loguru import logger

from sentence_transformers import SentenceTransformer


_MODEL_NAME = os.environ.get("MODEL_NAME", "jinaai/jina-embeddings-v3")
_model: SentenceTransformer | None = None


def _load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {_MODEL_NAME}")
        # trust_remote_code required for Jina v3
        _model = SentenceTransformer(_MODEL_NAME, trust_remote_code=True)
    return _model


def get_embedding_function() -> Callable[[List[str]], List[List[float]]]:
    model = _load_model()

    def _embed(texts: List[str]) -> List[List[float]]:
        embeddings = model.encode(texts, batch_size=16, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    return _embed

