from typing import List, Tuple, Dict, Any
import os
import re
from pathlib import Path

try:
    from pypdf import PdfReader  # preferred modern library
except Exception:
    PdfReader = None  # optional dependency

def auto_chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Automatically chunk text with intelligent splitting and overlap.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If this is not the last chunk, try to find a good break point
        if end < len(text):
            # Look for sentence endings, paragraph breaks, or natural breaks
            break_points = []
            
            # Look for sentence endings (., !, ?) followed by whitespace
            sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', text[start:end])]
            if sentence_breaks:
                break_points.extend([start + bp for bp in sentence_breaks])
            
            # Look for paragraph breaks (double newlines)
            para_breaks = [m.end() for m in re.finditer(r'\n\s*\n', text[start:end])]
            if para_breaks:
                break_points.extend([start + bp for bp in para_breaks])
            
            # Look for single newlines
            line_breaks = [m.end() for m in re.finditer(r'\n', text[start:end])]
            if line_breaks:
                break_points.extend([start + bp for bp in line_breaks])
            
            # Look for spaces
            space_breaks = [m.end() for m in re.finditer(r'\s+', text[start:end])]
            if space_breaks:
                break_points.extend([start + bp for bp in space_breaks])
            
            # Choose the best break point (closest to end but not too close to start)
            if break_points:
                # Filter break points that are not too close to start
                valid_breaks = [bp for bp in break_points if bp > start + chunk_size // 2]
                if valid_breaks:
                    end = max(valid_breaks)
                else:
                    # If no good break point found, use the closest one
                    end = max(break_points)
        
        # Extract the chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move to next chunk with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def parse_document_simple(file_path: str) -> Tuple[str, List[str]]:
    """
    Simple document parser that works with various file types.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Tuple of (full_text, chunks)
    """
    try:
        file_path = Path(file_path)
        
        # Handle different file types
        if file_path.suffix.lower() == '.txt':
            # Plain text files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.suffix.lower() == '.md':
            # Markdown files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.suffix.lower() == '.py':
            # Python files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.suffix.lower() == '.pdf' and PdfReader is not None:
            # Try to extract text from PDF
            try:
                reader = PdfReader(str(file_path))
                parts: List[str] = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    if text:
                        parts.append(text)
                content = "\n\n".join(parts).strip()
                if not content:
                    # No extractable text found
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    content = f"Binary PDF with no extractable text: {file_path.name} ({len(data)} bytes)"
            except Exception:
                # Fallback to binary notice
                with open(file_path, 'rb') as f:
                    data = f.read()
                content = f"Binary PDF (failed to extract text): {file_path.name} ({len(data)} bytes)"
        else:
            # Try to read as text, fallback to binary
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Binary file - read as bytes and convert to text representation
                with open(file_path, 'rb') as f:
                    data = f.read()
                content = f"Binary file: {file_path.name} ({len(data)} bytes)"
        
        # Clean up the content
        content = content.strip()
        
        # Create chunks using auto chunking
        chunks = auto_chunk_text(content)
        
        # Ensure we have at least one chunk
        if not chunks:
            chunks = [content] if content else ["Empty document"]
        
        return content, chunks
        
    except Exception as e:
        print(f"Document parsing failed: {e}")
        # Return a fallback chunk
        fallback_text = f"Error parsing document: {file_path}"
        return fallback_text, [fallback_text]

def optimize_chunks_for_embedding(chunks: List[str], target_size: int = 512) -> List[str]:
    """
    Optimize chunks for better embedding performance.
    
    Args:
        chunks: List of text chunks
        target_size: Target size for each chunk
        
    Returns:
        Optimized list of chunks
    """
    if not chunks:
        return []
    
    optimized_chunks = []
    
    for chunk in chunks:
        if len(chunk) <= target_size:
            optimized_chunks.append(chunk)
        else:
            # Split large chunks
            sub_chunks = auto_chunk_text(chunk, target_size, overlap=25)
            optimized_chunks.extend(sub_chunks)
    
    return optimized_chunks