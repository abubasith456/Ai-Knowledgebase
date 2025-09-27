from typing import List
from app.config import settings


def create_chunks(text: str, chunk_ratio: float, overlap_ratio: float) -> List[str]:
    """Create overlapping text chunks"""
    if not text.strip():
        return []

    chunk_size = int(settings.DEFAULT_CHUNK_SIZE * chunk_ratio)
    overlap_size = int(chunk_size * overlap_ratio)

    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks
