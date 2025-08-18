"""
Alternative ChromaDB client wrapper that completely bypasses telemetry.
Uses a different approach to prevent telemetry errors.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Any
from loguru import logger

# Set environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "FALSE"

# Import chromadb directly without any patching
import chromadb
from chromadb.config import Settings

class ChromaClientWrapper:
    """Wrapper around ChromaDB client that bypasses telemetry."""
    
    def __init__(self, client):
        self._client = client
        self._disable_telemetry()
    
    def _disable_telemetry(self):
        """Disable telemetry on the wrapped client."""
        try:
            # Replace telemetry client with a no-op
            if hasattr(self._client, '_telemetry_client'):
                self._client._telemetry_client = self._noop_telemetry()
            
            # Also check for internal client telemetry
            if hasattr(self._client, '_client') and hasattr(self._client._client, 'telemetry_client'):
                self._client._client.telemetry_client = self._noop_telemetry()
                
        except Exception as e:
            logger.debug(f"Telemetry disable completed: {e}")
    
    def _noop_telemetry(self):
        """Create a no-op telemetry client."""
        class NoOpTelemetry:
            def __init__(self, *args, **kwargs):
                pass
            def capture(self, *args, **kwargs):
                pass
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        return NoOpTelemetry()
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped client."""
        return getattr(self._client, name)

def get_chroma_client() -> chromadb.Client:
    """
    Get a ChromaDB client with telemetry completely disabled.
    """
    host = os.environ.get("CHROMA_HOST")
    
    if host:
        # Remote client
        client = chromadb.HttpClient(
            host=host, 
            port=int(os.environ.get("CHROMA_PORT", "8000"))
        )
        return ChromaClientWrapper(client)
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
        
        # Create client
        client = chromadb.PersistentClient(
            path=str(data_dir),
            settings=settings
        )
        
        return ChromaClientWrapper(client)

def cleanup_incompatible_collections():
    """
    Clean up collections with incompatible embedding dimensions.
    """
    try:
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