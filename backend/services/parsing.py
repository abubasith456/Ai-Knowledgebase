from typing import List, Tuple
import os
from .index import parse_document_simple, auto_chunk_text

# TODO: replace with a real embedder (e.g., sentence-transformers) for production
def embed_texts(texts: List[str]) -> List[List[float]]:
    # Very simple placeholder embedding for demo; not suitable for production
    return [[float(len(t) % 7)] * 8 for t in texts]


def parse_with_docling(file_path: str) -> Tuple[str, List[str]]:
    """Parse document using our custom auto-chunking parser"""
    try:
        # Use our new auto-chunking parser instead of docling
        content, chunks = parse_document_simple(file_path)
        
        # Optimize chunks for better embedding performance
        optimized_chunks = auto_chunk_text(content, chunk_size=512, overlap=50)
        
        # Ensure we have at least one chunk
        if not optimized_chunks:
            optimized_chunks = [content] if content else ["Empty document"]
            
        return content, optimized_chunks
    except Exception as e:
        print(f"Document parsing failed: {e}")
        # Fallback to basic parsing if our parser fails
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "rb") as f:
                data = f.read()
            content = f"Parsed {len(data)} bytes from {file_path}"
        
        # Use auto-chunking for fallback as well
        chunks = auto_chunk_text(content, chunk_size=512, overlap=50)
        if not chunks:
            chunks = [content] if content else ["Empty document"]
        
        return content, chunks


def build_embeddings_from_chunks(chunks: List[str]) -> List[List[float]]:
    return embed_texts(chunks)
