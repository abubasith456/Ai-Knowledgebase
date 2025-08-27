from typing import List, Tuple
import os

# TODO: replace with a real embedder (e.g., sentence-transformers) for production
def embed_texts(texts: List[str]) -> List[List[float]]:
    # Very simple placeholder embedding for demo; not suitable for production
    return [[float(len(t) % 7)] * 8 for t in texts]


def parse_with_docling(file_path: str) -> Tuple[str, List[str]]:
    """Parse document using Docling DocumentConverter with OCR support"""
    try:
        # Import here to avoid circular imports
        from docling.document_converter import DocumentConverter
        
        # Use the new DocumentConverter API
        converter = DocumentConverter()
        doc = converter.convert(file_path).document
        
        # Export to markdown
        markdown_content = doc.export_to_markdown()
        
        # Create chunks from markdown content (512 characters each)
        chunks = []
        for i in range(0, len(markdown_content), 512):
            chunk = markdown_content[i:i + 512]
            if chunk.strip():
                chunks.append(chunk)
        
        # Ensure at least one chunk
        if not chunks:
            chunks = [markdown_content] if markdown_content.strip() else ["Empty document"]
            
        return markdown_content, chunks
    except Exception as e:
        print(f"Docling parsing failed: {e}")
        # Fallback to basic parsing if Docling fails
        with open(file_path, "rb") as f:
            data = f.read()
        text = f"Parsed {len(data)} bytes from {file_path}"
        chunks = [text[i : i + 512] for i in range(0, len(text), 512)] or [text]
        return text, chunks


def build_embeddings_from_chunks(chunks: List[str]) -> List[List[float]]:
    return embed_texts(chunks)
