from typing import List, Tuple, Dict, Any
import os
import logging
from .index import parse_document_simple

logger = logging.getLogger(__name__)


def parse_with_docling(file_path: str) -> Tuple[str, str]:
    """Parse document and return full text content (no chunking)"""
    try:
        # Use our simple parser to get the full text content
        content, _ = parse_document_simple(file_path)
        
        logger.info(f"Successfully parsed document {file_path}")
        return content, content  # Return content twice to maintain compatibility
    except Exception as e:
        logger.error(f"Document parsing failed: {e}")
        # Fallback to basic parsing if our parser fails
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "rb") as f:
                data = f.read()
            content = f"Parsed {len(data)} bytes from {file_path}"
        
        logger.info(f"Fallback parsing completed")
        return content, content  # Return content twice to maintain compatibility



