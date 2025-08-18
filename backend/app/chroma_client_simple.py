"""
Simple ChromaDB client wrapper that suppresses telemetry errors.
Uses stderr redirection to hide telemetry error messages.
"""

import os
import sys
import contextlib
from pathlib import Path
from typing import Optional
from loguru import logger

# Set environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "FALSE"

# Import chromadb
import chromadb
from chromadb.config import Settings

@contextlib.contextmanager
def suppress_telemetry_errors():
    """Context manager to suppress telemetry error messages."""
    # Redirect stderr to suppress telemetry errors
    old_stderr = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr

def get_chroma_client() -> chromadb.Client:
    """
    Get a ChromaDB client with telemetry errors suppressed.
    """
    host = os.environ.get("CHROMA_HOST")
    
    if host:
        # Remote client
        with suppress_telemetry_errors():
            return chromadb.HttpClient(
                host=host, 
                port=int(os.environ.get("CHROMA_PORT", "8000"))
            )
    else:
        # Local persistent client
        data_dir = Path(os.environ.get("CHROMA_DATA_DIR") or "./data/chroma")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using local ChromaDB storage at: {data_dir}")
        
        # Create settings with telemetry disabled
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
        
        # Create client with telemetry errors suppressed
        with suppress_telemetry_errors():
            client = chromadb.PersistentClient(
                path=str(data_dir),
                settings=settings
            )
        
        return client

def cleanup_incompatible_collections():
    """
    Clean up collections with incompatible embedding dimensions.
    """
    try:
        with suppress_telemetry_errors():
            client = get_chroma_client()
            collections = client.list_collections()
            
            cleaned_count = 0
            for collection in collections:
                try:
                    # Test if collection is compatible
                    collection.get()
                    logger.debug(f"Collection {collection.name} is compatible")
                except Exception as e:
                    if "Embedding dimension" in str(e):
                        logger.info(f"Deleting incompatible collection: {collection.name}")
                        try:
                            client.delete_collection(name=collection.name)
                            cleaned_count += 1
                        except Exception as delete_error:
                            logger.warning(f"Failed to delete collection {collection.name}: {delete_error}")
                    else:
                        logger.debug(f"Collection {collection.name} check: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} incompatible collections")
        
    except Exception as e:
        logger.warning(f"Collection cleanup error: {e}")

# Run cleanup on module import
cleanup_incompatible_collections()