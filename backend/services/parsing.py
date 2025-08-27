from typing import List, Tuple


# TODO: replace with a real embedder (e.g., sentence-transformers) for production
def embed_texts(texts: List[str]) -> List[List[float]]:
    # Very simple placeholder embedding for demo; not suitable for production
    return [[float(len(t) % 7)] * 8 for t in texts]


# Plug your automatic Docling parser here. Keep the (text, chunks) return signature.
def parse_with_docling(file_path: str) -> Tuple[str, List[str]]:
    # Example placeholder parse: read bytes and create a fake "parsed" text split to chunks
    with open(file_path, "rb") as f:
        data = f.read()
    text = f"Parsed {len(data)} bytes from {file_path}"
    chunks = [text[i : i + 512] for i in range(0, len(text), 512)] or [text]
    return text, chunks


def build_embeddings_from_chunks(chunks: List[str]) -> List[List[float]]:
    return embed_texts(chunks)
