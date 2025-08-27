from typing import List, Tuple
import os
from docling import DocumentParser


# TODO: replace with a real embedder (e.g., sentence-transformers) for production
def embed_texts(texts: List[str]) -> List[List[float]]:
    # Very simple placeholder embedding for demo; not suitable for production
    return [[float(len(t) % 7)] * 8 for t in texts]


# Plug your automatic Docling parser here. Keep the (text, chunks) return signature.
def parse_with_docling(file_path: str) -> Tuple[str, List[str]]:
    """Parse document using Docling with OCR support"""
    try:
        parser = DocumentParser()
        doc = parser.parse(file_path)
        
        # Extract full text
        full_text = doc.text
        
        # Create chunks (512 characters each)
        chunks = []
        for i in range(0, len(full_text), 512):
            chunk = full_text[i:i + 512]
            if chunk.strip():
                chunks.append(chunk)
        
        # Ensure at least one chunk
        if not chunks:
            chunks = [full_text] if full_text.strip() else ["Empty document"]
            
        return full_text, chunks
    except Exception as e:
        # Fallback to basic parsing if Docling fails
        with open(file_path, "rb") as f:
            data = f.read()
        text = f"Parsed {len(data)} bytes from {file_path}"
        chunks = [text[i : i + 512] for i in range(0, len(text), 512)] or [text]
        return text, chunks


def build_embeddings_from_chunks(chunks: List[str]) -> List[List[float]]:
    return embed_texts(chunks)
